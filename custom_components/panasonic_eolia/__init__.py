"""Example of a custom component exposing a service."""
from __future__ import annotations

import logging
import os
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
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
PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: PanasonicEoliaConfigEntry) -> bool:
    """Set up Panasonic Eolia from a config entry."""
    _LOGGER.debug("async_setup_entry called")

    _LOGGER.info(f"entry -- {entry}")
    _LOGGER.info(f"hass -- {hass}")

    _LOGGER.info(f"entry data -- {entry.data}")
    auth_method = entry.data['auth_method']
    access_token = entry.data['access_token']
    refresh_token = entry.data['refresh_token']


    # Store client and coordinator in hass.data for platform access
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    session = get_async_client(hass)
    _LOGGER.info("Got aiohttp session from Home Assistant")

    if access_token != "" and refresh_token != "":
        auth = PanasonicEolia(access_token=access_token, refresh_token=refresh_token, session=session)
    else:
        raise ValueError(f"Invalid auth method: {auth_method}")

    # todo: token refresh using refresh token

    userinfo = await auth.get_userinfo()
    if userinfo is None:
        _LOGGER.info("Access token invalid, attempting refresh")
        refreshed = await auth.refresh_access_token()
        if not refreshed:
            raise ConfigEntryAuthFailed("Authentication failed when fetching userinfo")

        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                "access_token": auth.access_token,
                "refresh_token": auth.refresh_token,
            },
        )

        userinfo = await auth.get_userinfo()
        if userinfo is None:
            raise ConfigEntryAuthFailed("Authentication failed after token refresh")

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
