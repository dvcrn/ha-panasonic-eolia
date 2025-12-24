"""Config flow for Panasonic Eolia integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.httpx_client import get_async_client

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

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle re-authentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        auth_method = entry_data.get("auth_method")
        if auth_method == "password":
            return await self.async_step_reauth_password()
        if auth_method == "token":
            return await self.async_step_reauth_token()
        return self.async_show_menu(
            step_id="reauth",
            menu_options=["reauth_password", "reauth_token"],
        )

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
        return await self._async_handle_password_auth(
            user_input=user_input,
            step_id="password",
            reauth=False,
        )

    async def async_step_reauth_password(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle username/password re-authentication."""
        return await self._async_handle_password_auth(
            user_input=user_input,
            step_id="reauth_password",
            reauth=True,
        )

    async def _async_handle_password_auth(
        self,
        user_input: dict[str, Any] | None,
        step_id: str,
        reauth: bool,
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                session = get_async_client(self.hass)
                eolia = PanasonicEolia(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                    session=session,
                )
                _LOGGER.info("Trying to authenticate with username/password")

                response = await eolia.authenticate()
                _LOGGER.info("Authentication response: %s", response)

                if response is True:
                    _LOGGER.info("Authentication successful")

                    if reauth:
                        reauth_entry = getattr(self, "_reauth_entry", None)
                        if reauth_entry is None:
                            errors["base"] = "unknown"
                        else:
                            self.hass.config_entries.async_update_entry(
                                reauth_entry,
                                data={
                                    "auth_method": "password",
                                    CONF_USERNAME: user_input[CONF_USERNAME],
                                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                                    CONF_ACCESS_TOKEN: eolia.access_token,
                                    "refresh_token": eolia.refresh_token,
                                },
                            )
                            return self.async_abort(reason="reauth_successful")

                        return self.async_show_form(
                            step_id=step_id,
                            data_schema=STEP_PASSWORD_DATA_SCHEMA,
                            errors=errors,
                        )

                    await self.async_set_unique_id(user_input[CONF_USERNAME])
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"Panasonic Eolia ({user_input[CONF_USERNAME]})",
                        data={
                            "auth_method": "password",
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_ACCESS_TOKEN: eolia.access_token,
                            "refresh_token": eolia.refresh_token,
                        },
                    )

                _LOGGER.error("Authentication failed")
                errors["base"] = "invalid_auth"

            except Exception:
                _LOGGER.exception("Error during authentication")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id=step_id,
            data_schema=STEP_PASSWORD_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_token(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle token-based authentication."""
        return await self._async_handle_token_auth(
            user_input=user_input,
            step_id="token",
            reauth=False,
        )

    async def async_step_reauth_token(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle token-based re-authentication."""
        return await self._async_handle_token_auth(
            user_input=user_input,
            step_id="reauth_token",
            reauth=True,
        )

    async def _async_handle_token_auth(
        self,
        user_input: dict[str, Any] | None,
        step_id: str,
        reauth: bool,
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                session = get_async_client(self.hass)
                eolia = PanasonicEolia(
                    access_token=user_input["access_token"],
                    refresh_token=user_input["refresh_token"],
                    session=session,
                )
                _LOGGER.info("Trying to authenticate with tokens")

                devices = await eolia.get_devices()

                if devices is not None:
                    _LOGGER.info(
                        "Token authentication successful, found %d devices",
                        len(devices),
                    )

                    access_token = eolia.access_token or user_input["access_token"]
                    refresh_token = eolia.refresh_token or user_input["refresh_token"]

                    if reauth:
                        reauth_entry = getattr(self, "_reauth_entry", None)
                        if reauth_entry is None:
                            errors["base"] = "unknown"
                        else:
                            self.hass.config_entries.async_update_entry(
                                reauth_entry,
                                data={
                                    "auth_method": "token",
                                    "access_token": access_token,
                                    "refresh_token": refresh_token,
                                },
                            )
                            return self.async_abort(reason="reauth_successful")

                        return self.async_show_form(
                            step_id=step_id,
                            data_schema=STEP_TOKEN_DATA_SCHEMA,
                            errors=errors,
                        )

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

                _LOGGER.error(
                    "Token authentication failed - could not fetch devices"
                )
                errors["base"] = "invalid_auth"

            except Exception:
                _LOGGER.exception("Error during token authentication")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id=step_id,
            data_schema=STEP_TOKEN_DATA_SCHEMA,
            errors=errors,
        )
