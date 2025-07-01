"""Example of a custom component exposing a service."""
from __future__ import annotations

import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.panasonic_eolia.eolia_data import EoliaData

from .const import DOMAIN
from .eolia.auth import PanasonicEolia

# type PanasonicEoliaConfigEntry = ConfigEntry[PanasonicEolia]

class EoliaDataUpdateCoordinator(DataUpdateCoordinator[EoliaData]):
    def __init__(self) -> None:
        _LOGGER.debug("EoliaDataUpdateCoordinator initialized")
        super().__init__()

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

    session = get_async_client(hass)
    _LOGGER.info("Got aiohttp session from Home Assistant")

    password = os.environ.get('PANASONIC_PASSWORD', "")
    username_hex = os.environ.get('PANASONIC_USERNAME', "")

    username = bytes.fromhex(username_hex).decode('utf-8')
    _LOGGER.info(f"Decoded username: {username}")
    _LOGGER.info(f"Using password from: {'environment variable' if 'PANASONIC_PASSWORD' in os.environ else 'hardcoded value'}")

    auth = PanasonicEolia(username, password, session=session)
    if await auth.authenticate():
        _LOGGER.info("\nAuthentication successful!")

        # data_class = EoliaData(
        #     eolia=auth
        # )

        _LOGGER.debug(entry.data)

        # entry.runtime_data = data_class

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
