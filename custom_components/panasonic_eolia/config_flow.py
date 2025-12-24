"""Config flow for Panasonic Eolia integration."""
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from custom_components.panasonic_eolia.eolia.auth import PanasonicEolia

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_PASSWORD_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

STEP_TOKEN_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("access_token"): str,
        vol.Required("refresh_token"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Panasonic Eolia."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - show authentication method selection menu."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["password", "token"],
        )

    async def async_step_password(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle username/password authentication."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Try to authenticate
                eolia = PanasonicEolia(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD]
                )
                _LOGGER.info("Trying to authenticate with username/password")

                response = await eolia.authenticate()
                _LOGGER.info("Authentication response: %s", response)

                if response is True:
                    _LOGGER.info("Authentication successful")

                    # Create unique ID based on username
                    await self.async_set_unique_id(user_input[CONF_USERNAME])
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"Panasonic Eolia ({user_input[CONF_USERNAME]})",
                        data={
                            "auth_method": "password",
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_ACCESS_TOKEN: eolia.access_token,
                            'refresh_token': eolia.refresh_token,
                        },
                    )
                else:
                    _LOGGER.error("Authentication failed")
                    errors["base"] = "invalid_auth"

            except Exception as e:
                _LOGGER.error("Error during authentication: %s", e)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="password",
            data_schema=STEP_PASSWORD_DATA_SCHEMA,
            errors=errors
        )

    async def async_step_token(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle token-based authentication."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Try to authenticate with tokens
                eolia = PanasonicEolia(
                    access_token=user_input["access_token"],
                    refresh_token=user_input["refresh_token"]
                )
                _LOGGER.info("Trying to authenticate with tokens")

                # Test the tokens by fetching devices
                devices = await eolia.get_devices()

                if devices is not None:
                    _LOGGER.info("Token authentication successful, found %d devices", len(devices))

                    access_token = eolia.access_token or user_input["access_token"]
                    refresh_token = eolia.refresh_token or user_input["refresh_token"]

                    # Create unique ID based on the first part of access token
                    # (tokens don't have username, so we use part of token as ID)
                    unique_id = f"token_{access_token[:16]}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="Panasonic Eolia (Token Auth)",
                        data={
                            "auth_method": "token",
                            "access_token": access_token,
                            "refresh_token": refresh_token,
                        },
                    )
                else:
                    _LOGGER.error("Token authentication failed - could not fetch devices")
                    errors["base"] = "invalid_auth"

            except Exception as e:
                _LOGGER.error("Error during token authentication: %s", e)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="token",
            data_schema=STEP_TOKEN_DATA_SCHEMA,
            errors=errors
        )
