#!/usr/bin/env python3
"""
Panasonic Eolia Air Conditioner API Authentication Script

This script performs the complete OAuth flow to authenticate with the Panasonic API
and obtain an access token that can be used to call the devices endpoint.
"""

import base64
import hashlib
import logging
import re
import secrets
import urllib.parse
from datetime import datetime
from typing import List, Optional

import httpx

from .device import Appliance
from .requests import UpdateDeviceRequest
from .responses import (
    DevicesResponse,
    DeviceStatus,
    ProductFunctionsResponse,
)

logging.basicConfig()

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class PanasonicEolia:
    def __init__(self, username, password, session: Optional[httpx.AsyncClient] = None):
        if session:
            self.session = session
        else:
            _LOGGER.warning("no session provided, using default one")
            # Create client with cookie support and longer timeout
            self.session = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                follow_redirects=False  # We handle redirects manually
            )

        self.username = username
        self.password = password
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1'
        })

        # OAuth client details
        self.client_id = "JpNCoLeXs4rPMhWmnOjbOxat7MWTZEgr"
        self.redirect_uri = "com.panasonic.jp.SmartRAC://auth.digital.panasonic.com/ios/com.panasonic.jp.SmartRAC/callback"
        self.audience = "https://club.panasonic.jp/JpNCoLeXs4rPMhWmnOjbOxat7MWTZEgr/api/v1/"
        self.scope = "openid offline_access eolia.control"

        # Generate PKCE challenge
        self.code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        self.code_challenge = code_challenge

        # Generate state
        self.state = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

    async def step1_authorize(self):
        """Step 1: Initial authorization request"""
        _LOGGER.debug("Step 1: Initial authorization request...")

        params = {
            'code_challenge_method': 'S256',
            'scope': self.scope,
            'redirect_uri': self.redirect_uri,
            'code_challenge': self.code_challenge,
            'client_id': self.client_id,
            'audience': self.audience,
            'response_type': 'code',
            'state': self.state,
            'auth0Client': 'eyJ2ZXJzaW9uIjoiMS4zOS4xIiwibmFtZSI6IkF1dGgwLnN3aWZ0IiwiZW52Ijp7InZpZXciOiJhc3dhcyIsImlPUyI6IjE4LjYiLCJzd2lmdCI6IjUueCJ9fQ'
        }

        response = await self.session.get(
            'https://auth.digital.panasonic.com/authorize',
            params=params,
            follow_redirects=False
        )

        if response.status_code != 302:
            raise Exception(f"Expected redirect, got {response.status_code}")

        # Extract state from redirect
        location = response.headers.get('Location')
        state_match = re.search(r'state=([^&]+)', location)
        if state_match:
            self.auth_state = urllib.parse.unquote(state_match.group(1))
        else:
            raise Exception("Could not extract state from redirect")

        return True

    async def step2_login_page(self):
        """Step 2: Get login page"""
        _LOGGER.debug("Step 2: Getting login page...")

        # Follow the redirect to login page
        response = await self.session.get(
            'https://auth.digital.panasonic.com/login',
            params={
                'state': self.auth_state,
                'client': self.client_id,
                'protocol': 'oauth2',
                'code_challenge_method': 'S256',
                'scope': urllib.parse.quote(self.scope),
                'redirect_uri': urllib.parse.quote(self.redirect_uri),
                'code_challenge': self.code_challenge,
                'audience': urllib.parse.quote(self.audience),
                'response_type': 'code',
                'auth0Client': 'eyJ2ZXJzaW9uIjoiMS4zOS4xIiwibmFtZSI6IkF1dGgwLnN3aWZ0IiwiZW52Ijp7InZpZXciOiJhc3dhcyIsIklPUyI6IjE4LjYiLCJzd2lmdCI6IjUueCJ9fQ'
            }
        )

        # Debug: Save response to file
        with open('login_response.html', 'w') as f:
            f.write(response.text)

        # Extract CSRF token from response
        # Try multiple patterns
        patterns = [
            r'name="_csrf"\s+value="([^"]+)"',
            r'"csrf":"([^"]+)"',
            r'window\.guardian\.csrfToken\s*=\s*["\']([^"\']+)["\']',
            r'var\s+csrfToken\s*=\s*["\']([^"\']+)["\']',
            r'csrfToken["\']?\s*:\s*["\']([^"\']+)["\']'
        ]

        csrf_token = None
        for pattern in patterns:
            csrf_match = re.search(pattern, response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                _LOGGER.debug(f"Found CSRF token with pattern: {pattern}")
                break

        if csrf_token:
            self.csrf_token = csrf_token
        else:
            # Generate a dummy CSRF token if not found (some implementations accept any value)
            self.csrf_token = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
            _LOGGER.debug("Warning: Could not extract CSRF token, using generated value")

        return True

    async def step3_challenge(self):
        """Step 3: Get challenge"""
        _LOGGER.debug("Step 3: Getting challenge...")

        response = await self.session.post(
            'https://auth.digital.panasonic.com/usernamepassword/challenge',
            headers={
                'Content-Type': 'application/json',
                'Auth0-Client': 'eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xOS4yIn0=',
                'Origin': 'https://auth.digital.panasonic.com',
                'Referer': 'https://auth.digital.panasonic.com/'
            },
            json={
                'state': self.auth_state
            }
        )

        if response.status_code != 200:
            raise Exception(f"Challenge failed with status {response.status_code}")

        return True

    async def step4_login(self):
        """Step 4: Perform login"""
        _LOGGER.debug("Step 4: Performing login...")

        # Convert username to hex (as seen in the dump)
        username_hex = self.username.encode('utf-8').hex()

        login_data = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'tenant': 'pdpauth-a1',
            'response_type': 'code',
            'scope': self.scope,
            'audience': self.audience,
            '_csrf': self.csrf_token,
            'state': self.auth_state,
            '_intstate': 'deprecated',
            'username': username_hex,
            'password': self.password,
            'captcha': None,
            'connection': 'CLUBPanasonic-Authentication'
        }

        response = await self.session.post(
            'https://auth.digital.panasonic.com/usernamepassword/login',
            headers={
                'Content-Type': 'application/json',
                'Auth0-Client': 'eyJuYW1lIjoiYXV0aDAuanMtdWxwIiwidmVyc2lvbiI6IjkuMTkuMiJ9',
                'Origin': 'https://auth.digital.panasonic.com',
                'Referer': 'https://auth.digital.panasonic.com/'
            },
            json=login_data
        )

        _LOGGER.debug(f"Login response status: {response.status_code}")

        if response.status_code != 200:
            raise Exception(f"Login failed with status {response.status_code}: {response.text}")

        # The response is an HTML form that needs to be submitted
        # Extract form data
        wa_match = re.search(r'name="wa"\s+value="([^"]+)"', response.text)
        wresult_match = re.search(r'name="wresult"\s+value="([^"]+)"', response.text)
        wctx_match = re.search(r'name="wctx"\s+value="([^"]+)"', response.text)

        if not (wa_match and wresult_match and wctx_match):
            raise Exception("Could not extract form data from login response")

        # HTML decode the values
        import html
        wa = html.unescape(wa_match.group(1))
        wresult = html.unescape(wresult_match.group(1))
        wctx = html.unescape(wctx_match.group(1))

        return await self.step4b_callback(wa, wresult, wctx)

    async def step4b_callback(self, wa, wresult, wctx):
        """Step 4b: Submit the callback form"""
        _LOGGER.debug("Step 4b: Submitting callback...")

        callback_data = {
            'wa': wa,
            'wresult': wresult,
            'wctx': wctx
        }

        response = await self.session.post(
            'https://auth.digital.panasonic.com/login/callback',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'null',
                'Referer': 'https://auth.digital.panasonic.com/'
            },
            data=callback_data,
            follow_redirects=False
        )

        _LOGGER.debug(f"Callback response status: {response.status_code}")

        if response.status_code == 302:
            # Check if we need to follow to /authorize/resume
            location = response.headers.get('Location')
            if location and '/authorize/resume' in location:
                # Extract state parameter
                state_match = re.search(r'state=([^&]+)', location)
                if state_match:
                    resume_state = state_match.group(1)
                    return await self.step4c_authorize_resume(resume_state)
                else:
                    raise Exception("Could not extract state from resume redirect")
            else:
                raise Exception(f"Unexpected redirect location: {location}")
        else:
            raise Exception(f"Callback failed with status {response.status_code}")

    async def step4c_authorize_resume(self, resume_state):
        """Step 4c: Follow the authorize/resume redirect"""
        _LOGGER.debug("Step 4c: Following authorize/resume...")

        response = await self.session.get(
            'https://auth.digital.panasonic.com/authorize/resume',
            params={'state': resume_state},
            follow_redirects=False
        )

        _LOGGER.debug(f"Resume response status: {response.status_code}")
        _LOGGER.debug(f"Resume response headers: {dict(response.headers)}")

        if response.status_code == 302:
            # This should redirect to the app callback with the code
            location = response.headers.get('Location')
            if location:
                _LOGGER.debug(f"Resume redirect location: {location}")
                
                # Check if this is a cookie attachment redirect
                if 'cookie/attachContentToken' in location:
                    _LOGGER.debug("Got cookie attachment redirect, following it...")
                    # Follow the cookie attachment redirect
                    cookie_response = await self.session.get(
                        location,
                        follow_redirects=False
                    )
                    _LOGGER.debug(f"Cookie attachment response status: {cookie_response.status_code}")
                    _LOGGER.debug(f"Cookie attachment response headers: {dict(cookie_response.headers)}")
                    
                    if cookie_response.status_code == 302:
                        next_location = cookie_response.headers.get('Location')
                        if next_location and '/authorize' in next_location:
                            _LOGGER.debug("Got redirect back to authorize, following it...")
                            # Follow the authorize redirect
                            auth_response = await self.session.get(
                                next_location,
                                follow_redirects=False
                            )
                            _LOGGER.debug(f"Final authorize response status: {auth_response.status_code}")
                            _LOGGER.debug(f"Final authorize response headers: {dict(auth_response.headers)}")
                            
                            if auth_response.status_code == 302:
                                final_location = auth_response.headers.get('Location')
                                if final_location:
                                    _LOGGER.debug(f"Final redirect location: {final_location}")
                                    code_match = re.search(r'code=([^&]+)', final_location)
                                    if code_match:
                                        self.auth_code = code_match.group(1)
                                        _LOGGER.debug(f"Got authorization code: {self.auth_code[:10]}...")
                                        return True
                                    else:
                                        raise Exception(f"Could not extract authorization code from final redirect: {final_location}")
                            else:
                                raise Exception(f"Final authorize failed with status {auth_response.status_code}")
                        elif next_location:
                            # Check if the code is in this redirect
                            code_match = re.search(r'code=([^&]+)', next_location)
                            if code_match:
                                self.auth_code = code_match.group(1)
                                _LOGGER.debug(f"Got authorization code: {self.auth_code[:10]}...")
                                return True
                            else:
                                raise Exception(f"Could not extract authorization code from redirect: {next_location}")
                    else:
                        raise Exception(f"Cookie attachment failed with status {cookie_response.status_code}")
                else:
                    # Try to extract code directly
                    code_match = re.search(r'code=([^&]+)', location)
                    if code_match:
                        self.auth_code = code_match.group(1)
                        _LOGGER.debug(f"Got authorization code: {self.auth_code[:10]}...")
                        return True
                    else:
                        raise Exception(f"Could not extract authorization code from redirect: {location}")
            else:
                raise Exception("Resume response missing Location header")
        else:
            raise Exception(f"Resume failed with status {response.status_code}")

    async def step5_token_exchange(self):
        """Step 5: Exchange authorization code for access token"""
        _LOGGER.debug("Step 5: Exchanging code for token...")

        token_data = {
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'code': self.auth_code,
            'grant_type': 'authorization_code',
            'code_verifier': self.code_verifier
        }

        response = await self.session.post(
            'https://auth.digital.panasonic.com/oauth/token',
            headers={
                'Content-Type': 'application/json',
                'Auth0-Client': 'eyJ2ZXJzaW9uIjoiMS4zOS4xIiwibmFtZSI6IkF1dGgwLnN3aWZ0IiwiZW52Ijp7InZpZXciOiJhc3dhcyIsIklPUyI6IjE4LjYiLCJzd2lmdCI6IjUueCJ9fQ'
            },
            json=token_data
        )

        if response.status_code != 200:
            raise Exception(f"Token exchange failed with status {response.status_code}: {response.text}")

        token_response = response.json()
        self.access_token = token_response['access_token']
        self.refresh_token = token_response['refresh_token']
        self.id_token = token_response['id_token']
        self.expires_in = token_response['expires_in']

        _LOGGER.debug(f"Successfully obtained access token (expires in {self.expires_in} seconds)")
        return True

    async def authenticate(self):
        """Perform the complete authentication flow"""
        try:
            await self.step1_authorize()
            await self.step2_login_page()
            await self.step3_challenge()
            await self.step4_login()
            await self.step5_token_exchange()
            return True
        except Exception as e:
            _LOGGER.debug(f"Authentication failed: {e}")
            return False

    async def get_devices(self) -> List[Appliance]:
        """Test the authentication by fetching devices"""
        _LOGGER.debug("\nFetching devices...")

        # Use Japan time (JST) for X-Eolia-Date
        from datetime import timedelta, timezone
        jst = timezone(timedelta(hours=9))
        current_time = datetime.now(jst).strftime('%Y-%m-%dT%H:%M:%S')

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/Json; charset=UTF-8',  # Note: capital J as in the dump
            'Accept': 'application/json',
            'X-Eolia-Date': current_time,
            'User-Agent': '%E3%82%A8%E3%82%AA%E3%83%AA%E3%82%A2/81 CFNetwork/3826.600.31 Darwin/24.6.0'
        }

        response = await self.session.get(
            'https://app.rac.apws.panasonic.com/eolia/v6/devices',
            headers=headers
        )

        if response.status_code == 200:
            devices = response.json()
            return DevicesResponse.from_dict(devices).ac_list
        else:
            _LOGGER.debug(f"Failed to fetch devices: {response.status_code} - {response.text}")
            return None

    async def get_product_functions(self, product_code: str):
        """Get function list for a specific product"""
        _LOGGER.debug(f"\nFetching functions for product {product_code}...")

        # Use Japan time (JST) for X-Eolia-Date
        from datetime import timedelta, timezone
        jst = timezone(timedelta(hours=9))
        current_time = datetime.now(jst).strftime('%Y-%m-%dT%H:%M:%S')

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/Json; charset=UTF-8',  # Note: capital J as in the dump
            'Accept': 'application/json',
            'X-Eolia-Date': current_time,
            'User-Agent': '%E3%82%A8%E3%82%AA%E3%83%AA%E3%82%A2/81 CFNetwork/3826.600.31 Darwin/24.6.0'
        }

        response = await self.session.get(
            f'https://app.rac.apws.panasonic.com/eolia/v6/products/{product_code}/functions',
            headers=headers
        )

        if response.status_code == 200:
            return ProductFunctionsResponse.from_dict(response.json())
        else:
            _LOGGER.debug(f"Failed to fetch product functions: {response.status_code} - {response.text}")
            return None

    async def get_device_status(self, device_id: str) -> DeviceStatus:
        """Get status for a specific device"""
        _LOGGER.debug(f"\nFetching status for device {device_id}...")

        # Use Japan time (JST) for X-Eolia-Date
        from datetime import timedelta, timezone
        jst = timezone(timedelta(hours=9))
        current_time = datetime.now(jst).strftime('%Y-%m-%dT%H:%M:%S')

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/Json; charset=UTF-8',  # Note: capital J as in the dump
            'Accept': 'application/json',
            'X-Eolia-Date': current_time,
            'User-Agent': '%E3%82%A8%E3%82%AA%E3%83%AA%E3%82%A2/81 CFNetwork/3826.600.31 Darwin/24.6.0'
        }

        # URL encode the device_id
        encoded_device_id = urllib.parse.quote(device_id, safe='')

        response = await self.session.get(
            f'https://app.rac.apws.panasonic.com/eolia/v6/devices/{encoded_device_id}/status',
            headers=headers
        )

        if response.status_code == 200:
            return DeviceStatus.from_dict(response.json())
        else:
            _LOGGER.debug(f"Failed to fetch device status: {response.status_code} - {response.text}")
            return None

    async def update_device_status(self, device_id: str, status: UpdateDeviceRequest):
        """Update device status by sending PUT request"""
        _LOGGER.debug(f"\nUpdating status for device {device_id}...")

        # Use Japan time (JST) for X-Eolia-Date
        from datetime import timedelta, timezone
        jst = timezone(timedelta(hours=9))
        current_time = datetime.now(jst).strftime('%Y-%m-%dT%H:%M:%S')

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/Json; charset=UTF-8',  # Note: capital J as in the dump
            'Accept': 'application/json',
            'X-Eolia-Date': current_time,
            'User-Agent': '%E3%82%A8%E3%82%AA%E3%83%AA%E3%82%A2/81 CFNetwork/3826.600.31 Darwin/24.6.0'
        }

        # URL encode the device_id
        encoded_device_id = urllib.parse.quote(device_id, safe='')

        # Convert status object to dict for JSON payload
        payload = status.to_dict()

        # Ensure we have an operation_token - it should come from the previous status response
        if 'operation_token' not in payload or payload['operation_token'] is None:
            _LOGGER.debug("Warning: No operation_token provided. You should use the token from the last status response.")
            # For now, we'll need to fetch the current status first
            current_status = await self.get_device_status(device_id)
            if current_status and current_status.operation_token:
                payload['operation_token'] = current_status.operation_token
            else:
                payload['operation_token'] = ""

        _LOGGER.debug(f"Full payload: {payload}")

        _LOGGER.debug(f"Full URL: https://app.rac.apws.panasonic.com/eolia/v6/devices/{encoded_device_id}/status")

        response = await self.session.put(
            f'https://app.rac.apws.panasonic.com/eolia/v6/devices/{encoded_device_id}/status',
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            _LOGGER.debug("Successfully updated device status")
            return DeviceStatus.from_dict(response.json())
        else:
            _LOGGER.debug(f"Failed to update device status: {response.status_code} - {response.text}")
            return None
