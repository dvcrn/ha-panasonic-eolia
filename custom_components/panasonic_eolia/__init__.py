"""Example of a custom component exposing a service."""
from __future__ import annotations

import logging
import os

from homeassistant.components.climate import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .eolia.auth import PanasonicEolia

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

# Use empty_config_schema because the component does not have any config options
CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)
PLATFORMS: list[Platform] = [Platform.CLIMATE]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Panasonic Eolia from a config entry."""
    _LOGGER.debug("async_setup_entry called")

    # Store client and coordinator in hass.data for platform access
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    session = async_get_clientsession(hass)
    _LOGGER.info("Got aiohttp session from Home Assistant")

    password = os.environ.get('PANASONIC_PASSWORD', "")
    username_hex = os.environ.get('PANASONIC_USERNAME', "")

    username = bytes.fromhex(username_hex).decode('utf-8')
    _LOGGER.info(f"Decoded username: {username}")
    _LOGGER.info(f"Using password from: {'environment variable' if 'PANASONIC_PASSWORD' in os.environ else 'hardcoded value'}")

    auth = PanasonicEolia(username, password, session=session)
    if auth.authenticate():
        _LOGGER.info("\nAuthentication successful!")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
