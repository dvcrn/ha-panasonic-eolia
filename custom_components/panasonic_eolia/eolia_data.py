from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.panasonic_eolia.eolia.auth import PanasonicEolia
from custom_components.panasonic_eolia.eolia.device import Appliance
from custom_components.panasonic_eolia.eolia.responses import DeviceStatus

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

type PanasonicEoliaConfigEntry = ConfigEntry[EoliaData]

@dataclass
class EoliaData:
    eolia: PanasonicEolia
    appliances: list[Appliance]

@dataclass
class EoliaApplianceData:
    appliance: Appliance
    status: DeviceStatus


_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

class EolliaApplianceDataCoordinator(DataUpdateCoordinator[EoliaApplianceData]):
    """Class to manage fetching data."""

    _appliance: Appliance
    _eolia: PanasonicEolia
    _appliance_status: DeviceStatus

    def __init__(self, hass: HomeAssistant, eolia: PanasonicEolia, appliance: Appliance) -> None:
        """Initialize coordinator."""

        self._eolia = eolia
        self._appliance = appliance

        super().__init__(
            hass,
            logger=_LOGGER,
            name="panasonic_eolia",
            update_interval=timedelta(seconds=15),
        )

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        _LOGGER.debug(f"[DataCoordinator] async_setup for {self._appliance.nickname}")
        if self._appliance.appliance_id:
            self._appliance_status = await self._eolia.get_device_status(self._appliance.appliance_id)

    async def _async_update_data(self):
        _LOGGER.debug(f"[DataCoordinator] async_update for {self._appliance.nickname}")
        if self._appliance.appliance_id:
            self._appliance_status = await self._eolia.get_device_status(self._appliance.appliance_id)

        return EoliaApplianceData(self._appliance, self._appliance_status)
