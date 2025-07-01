"""Example of a custom component exposing a service."""
from __future__ import annotations

import logging
import os
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.panasonic_eolia.climate import PanasonicEoliaClimate
from custom_components.panasonic_eolia.eolia.device import Appliance
from custom_components.panasonic_eolia.eolia.responses import DeviceStatus
from custom_components.panasonic_eolia.eolia_data import (
    EoliaApplianceData,
    EoliaData,
    PanasonicEoliaConfigEntry,
)

from .const import DOMAIN
from .eolia.auth import PanasonicEolia

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

SCAN_INTERVAL = timedelta(seconds=15)

# Use empty_config_schema because the component does not have any config options
CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)
PLATFORMS: list[Platform] = [Platform.CLIMATE]

async def async_setup_entry(hass: HomeAssistant, entry: PanasonicEoliaConfigEntry) -> bool:
    """Set up Panasonic Eolia from a config entry."""
    _LOGGER.debug("async_setup_entry called")

    # Store client and coordinator in hass.data for platform access
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    session = get_async_client(hass)
    _LOGGER.info("Got aiohttp session from Home Assistant")

    access_token = os.environ.get('PANASONIC_ACCESS_TOKEN', "")
    refresh_token = os.environ.get('PANASONIC_REFRESH_TOKEN', "")
    password = os.environ.get('PANASONIC_PASSWORD', "")
    username_hex = os.environ.get('PANASONIC_USERNAME', "")

    username = bytes.fromhex(username_hex).decode('utf-8')
    _LOGGER.info(f"Decoded username: {username}")
    _LOGGER.info(f"Using password from: {'environment variable' if 'PANASONIC_PASSWORD' in os.environ else 'hardcoded value'}")

    auth = PanasonicEolia(access_token=access_token, refresh_token=refresh_token, session=session)
    # auth = PanasonicEolia(username, password, session=session)
    # TODO: fix proper authentication with 2fa
    # if await auth.authenticate():

    devices = await auth.get_devices()

    data_class = EoliaData(
        eolia=auth,
        appliances=devices,
    )

    entry.runtime_data = data_class

    _LOGGER.debug("written runtime data ")
    _LOGGER.debug(entry.runtime_data)

    # entry.runtime_data = data_class

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
