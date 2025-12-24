from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.panasonic_eolia.eolia.auth import PanasonicEolia
from custom_components.panasonic_eolia.eolia.device import Appliance
from custom_components.panasonic_eolia.eolia.exceptions import (
    DeviceLockedByAnotherControllerException,
)
from custom_components.panasonic_eolia.eolia.requests import UpdateDeviceRequest
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

    # for update
    _operation_token: str
    _token_timestamp: datetime
    _token_ttl: timedelta = timedelta(minutes=2)

    def __init__(
        self, hass: HomeAssistant, eolia: PanasonicEolia, appliance: Appliance
    ) -> None:
        """Initialize coordinator."""

        self._eolia = eolia
        self._appliance = appliance
        self._appliance_status = None  # Initialize to prevent AttributeError
        self._operation_token = None
        self._token_timestamp = None

        super().__init__(
            hass,
            logger=_LOGGER,
            name="panasonic_eolia",
            update_interval=timedelta(seconds=15),
        )

    def _is_token_valid(self) -> bool:
        """Check if the current operation token is still valid (within TTL)."""
        if not self._operation_token or not self._token_timestamp:
            return False

        elapsed = datetime.now() - self._token_timestamp
        return elapsed < self._token_ttl

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        _LOGGER.debug(f"[DataCoordinator] async_setup for {self._appliance.nickname}")
        if self._appliance.appliance_id:
            self._appliance_status = await self._eolia.get_device_status(
                self._appliance.appliance_id
            )

    async def submit_update_request(self, update_request: UpdateDeviceRequest):
        _LOGGER.debug(
            f"[DataCoordinator] submit_update_request for {self._appliance.nickname}"
        )
        if self._appliance.appliance_id:
            # check if we have a valid token within TTL
            if self._is_token_valid():
                _LOGGER.debug(f"Using operation token: {self._operation_token}")
                update_request.operation_token = self._operation_token
            else:
                _LOGGER.debug("No valid operation token available or token expired")
                update_request.operation_token = None

            try:
                status = await self._eolia.update_device_status(
                    self._appliance.appliance_id, update_request
                )

                # if we receive a token back, we store it with timestamp
                if status and status.operation_token:
                    _LOGGER.debug(f"Received operation token: {status.operation_token}")
                    self._operation_token = status.operation_token
                    self._token_timestamp = datetime.now()

                return status
            except DeviceLockedByAnotherControllerException:
                _LOGGER.warning(
                    f"Device {self._appliance.nickname} is locked by another controller. Please wait 2 minutes."
                )
                # Clear our token since it's invalid
                self._operation_token = None
                self._token_timestamp = None
                # Re-raise the exception to be handled by the climate entity
                raise

    async def _async_update_data(self):
        _LOGGER.debug(f"[DataCoordinator] async_update for {self._appliance.nickname}")
        if self._appliance.appliance_id:
            self._appliance_status = await self._eolia.get_device_status(
                self._appliance.appliance_id
            )

        return EoliaApplianceData(self._appliance, self._appliance_status)

    async def _async_set_temperature(self, temperature: int):
        _LOGGER.debug(
            f"[DataCoordinator] async_set_temperature for {self._appliance.nickname}"
        )

        # Ensure we have a valid status before trying to update
        if self._appliance_status is None:
            _LOGGER.warning(
                f"[DataCoordinator] No status available for {self._appliance.nickname}, fetching current status"
            )
            if self._appliance.appliance_id:
                self._appliance_status = await self._eolia.get_device_status(
                    self._appliance.appliance_id
                )

            if self._appliance_status is None:
                _LOGGER.error(
                    f"[DataCoordinator] Failed to get status for {self._appliance.nickname}"
                )
                return None

        update_request = self._appliance_status.to_update_request()
        update_request.temperature = temperature
        return await self.submit_update_request(update_request)

    async def _async_set_off(self):
        _LOGGER.debug(f"[DataCoordinator] async_set_off for {self._appliance.nickname}")

        if self._appliance_status is None:
            _LOGGER.warning(
                f"[DataCoordinator] No status available for {self._appliance.nickname}, fetching current status"
            )
            if self._appliance.appliance_id:
                self._appliance_status = await self._eolia.get_device_status(
                    self._appliance.appliance_id
                )

        update_request = self._appliance_status.to_update_request()
        update_request.operation_status = False
        return await self.submit_update_request(update_request)

    async def _async_set_hvac_mode(self, operation_mode: str, operation_status: bool):
        _LOGGER.debug(
            f"[DataCoordinator] async_set_hvac_mode for {self._appliance.nickname}: mode={operation_mode}, status={operation_status}"
        )

        if self._appliance_status is None:
            _LOGGER.warning(
                f"[DataCoordinator] No status available for {self._appliance.nickname}, fetching current status"
            )
            if self._appliance.appliance_id:
                self._appliance_status = await self._eolia.get_device_status(
                    self._appliance.appliance_id
                )

            if self._appliance_status is None:
                _LOGGER.error(
                    f"[DataCoordinator] Failed to get status for {self._appliance.nickname}"
                )
                return None

        update_request = self._appliance_status.to_update_request()
        update_request.operation_mode = operation_mode
        update_request.operation_status = operation_status
        return await self.submit_update_request(update_request)

    async def _async_set_fan_mode(self, wind_volume: int = None, air_flow: str = None):
        _LOGGER.debug(
            f"[DataCoordinator] async_set_fan_mode for {self._appliance.nickname}: wind_volume={wind_volume}, air_flow={air_flow}"
        )

        if self._appliance_status is None:
            _LOGGER.warning(
                f"[DataCoordinator] No status available for {self._appliance.nickname}, fetching current status"
            )
            if self._appliance.appliance_id:
                self._appliance_status = await self._eolia.get_device_status(
                    self._appliance.appliance_id
                )

            if self._appliance_status is None:
                _LOGGER.error(
                    f"[DataCoordinator] Failed to get status for {self._appliance.nickname}"
                )
                return None

        update_request = self._appliance_status.to_update_request()
        if wind_volume is not None:
            update_request.wind_volume = wind_volume
        if air_flow is not None:
            update_request.air_flow = air_flow
        return await self.submit_update_request(update_request)

    async def _async_set_swing_mode(self, wind_direction: int):
        _LOGGER.debug(
            f"[DataCoordinator] async_set_swing_mode for {self._appliance.nickname}: wind_direction={wind_direction}"
        )

        if self._appliance_status is None:
            _LOGGER.warning(
                f"[DataCoordinator] No status available for {self._appliance.nickname}, fetching current status"
            )
            if self._appliance.appliance_id:
                self._appliance_status = await self._eolia.get_device_status(
                    self._appliance.appliance_id
                )

            if self._appliance_status is None:
                _LOGGER.error(
                    f"[DataCoordinator] Failed to get status for {self._appliance.nickname}"
                )
                return None

        update_request = self._appliance_status.to_update_request()
        update_request.wind_direction = wind_direction
        return await self.submit_update_request(update_request)

    async def _async_set_preset_mode(self, air_flow: str):
        _LOGGER.debug(
            f"[DataCoordinator] async_set_preset_mode for {self._appliance.nickname}: air_flow={air_flow}"
        )

        if self._appliance_status is None:
            _LOGGER.warning(
                f"[DataCoordinator] No status available for {self._appliance.nickname}, fetching current status"
            )
            if self._appliance.appliance_id:
                self._appliance_status = await self._eolia.get_device_status(
                    self._appliance.appliance_id
                )

            if self._appliance_status is None:
                _LOGGER.error(
                    f"[DataCoordinator] Failed to get status for {self._appliance.nickname}"
                )
                return None

        update_request = self._appliance_status.to_update_request()
        update_request.air_flow = air_flow
        # When setting preset, we should reset wind_volume to auto
        if air_flow in ["quiet", "powerful"]:
            update_request.wind_volume = 0  # AUTO
        return await self.submit_update_request(update_request)
