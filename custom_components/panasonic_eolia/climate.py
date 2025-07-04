import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    PRESET_BOOST,
    PRESET_NONE,
    PRESET_SLEEP,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.panasonic_eolia.eolia.auth import PanasonicEolia
from custom_components.panasonic_eolia.eolia.device import Appliance
from custom_components.panasonic_eolia.eolia.exceptions import (
    DeviceLockedByAnotherControllerException,
)
from custom_components.panasonic_eolia.eolia.responses import (
    AirFlow,
    DeviceStatus,
    OperationMode,
    WindDirection,
    WindVolume,
)
from custom_components.panasonic_eolia.eolia_data import (
    EolliaApplianceDataCoordinator,
    PanasonicEoliaConfigEntry,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

HVAC_MODE_MAP = {
    "Cooling": HVACMode.COOL,
    "Heating": HVACMode.HEAT,
    "Auto": HVACMode.HEAT_COOL,
    "CoolDehumidifying": HVACMode.DRY,
    "Blast": HVACMode.FAN_ONLY,
    "Stop": HVACMode.OFF,
}

HVAC_MODE_MAP_REVERSE = {v: k for k, v in HVAC_MODE_MAP.items()}

# Map fan modes to wind volume/air flow
FAN_MODE_TO_WIND_VOLUME = {
    "Low": WindVolume.LOW.value,
    "Medium": WindVolume.MEDIUM_HIGH.value,
    "Medium High": WindVolume.MEDIUM_HIGH.value,
    "High": WindVolume.HIGH.value,
    "Very High": WindVolume.VERY_HIGH.value,
    "Auto": WindVolume.AUTO.value,
}

FAN_MODE_TO_AIR_FLOW = {
    "Quiet": AirFlow.QUIET.value,
    "Max": AirFlow.POWERFUL.value,
}

# Map swing modes to wind direction
SWING_MODE_TO_WIND_DIRECTION = {
    "Auto": WindDirection.AUTO.value,
    "Top": WindDirection.TOP.value,
    "Middle Top": WindDirection.MIDDLE_TOP.value,
    "Middle": WindDirection.MIDDLE.value,
    "Middle Bottom": WindDirection.MIDDLE_BOTTOM.value,
    "Bottom": WindDirection.BOTTOM.value,
    "Swing": WindDirection.SWING.value,
}

# Map preset modes to air flow
PRESET_MODE_TO_AIR_FLOW = {
    PRESET_NONE: AirFlow.NOT_SET.value,
    PRESET_SLEEP: AirFlow.QUIET.value,
    PRESET_BOOST: AirFlow.POWERFUL.value,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: PanasonicEoliaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Panasonic Eolia climate platform."""
    _LOGGER.debug(dir(entry.runtime_data))
    _LOGGER.debug(entry.runtime_data)

    _LOGGER.debug(f"Climate async_setup_entry called, num devices: {len(entry.runtime_data.appliances)}")


    entities = []
    for device in entry.runtime_data.appliances:
        _LOGGER.info(f"discovered aircon {device.nickname}")
        coordinator = EolliaApplianceDataCoordinator(hass, entry.runtime_data.eolia, device)

        entity = PanasonicEoliaClimate(coordinator=coordinator, appliance=device, eolia=entry.runtime_data.eolia)
        await entity.query_device_state()
        entities.append(entity)

    async_add_entities(entities)

    # For now, create a dummy entity
    # Later this will use the coordinator from hass.data[DOMAIN][entry.entry_id]
    # async_add_entities([PanasonicEoliaClimate()])


class PanasonicEoliaClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Panasonic Eolia climate device."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.PRESET_MODE
        # | ClimateEntityFeature.SWING_HORIZONTAL_MODE
    )
    _appliance: Appliance
    _eolia: PanasonicEolia
    _last_device_status: DeviceStatus
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    _coordinator: EolliaApplianceDataCoordinator

    def __init__(self, coordinator: EolliaApplianceDataCoordinator, appliance: Appliance, eolia: PanasonicEolia) -> None:
        """Initialize the climate device."""
        _LOGGER.debug(f"Climate entity init called with appliance: {appliance.nickname}")
        super().__init__(coordinator=coordinator)

        # Temporary hardcoded values
        self._attr_unique_id = appliance.appliance_id
        self._attr_name = appliance.nickname

        self._eolia = eolia
        self._appliance = appliance

        self._coordinator = coordinator


        # State variables
        # self._current_temperature = 25.0
        # self._target_temperature = 22.0
        # self._hvac_mode = HVACMode.OFF
        # self._is_on = False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(f"handle_coordinator_update called with appliance: {self._appliance.nickname}")
        status = self.coordinator.data.status
        # appliance =self.coordinator.data["appliance"]

        self._last_device_status = status

        # self._attr_is_on = self.coordinator.data[self.idx]["state"]
        self.async_write_ha_state()

    @property
    def should_poll(self) -> bool:
        """Return True if entity should be polled."""
        return False

    async def async_update(self) -> None:
        """Update the entity."""
        await self.query_device_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        await self.query_device_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self._last_device_status is not None

    async def query_device_state(self):
        """Query the device state."""
        if self._appliance.appliance_id is not None:
            try:
                status = await self._eolia.get_device_status(self._appliance.appliance_id)
                _LOGGER.debug(f"Device status: {status}")
                _LOGGER.debug("Device status keys and values:")
                for key, value in vars(status).items():
                    _LOGGER.debug(f"  {key}: {value}")
                self._last_device_status = status
            except Exception as e:
                _LOGGER.error(f"Failed to query device state: {e}")

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        _LOGGER.debug(f"[{self._appliance.nickname}] hvac_mode() == {self._last_device_status.operation_mode}")
        if self._last_device_status.operation_mode  == OperationMode.OFF:
            return HVACMode.OFF
        elif self._last_device_status.operation_mode == OperationMode.COOLING:
            _LOGGER.debug(f"[{self._appliance.nickname}] hvac_mode is COOL")
            return HVACMode.COOL
        elif self._last_device_status.operation_mode == OperationMode.HEATING:
            return HVACMode.HEAT
        elif self._last_device_status.operation_mode == OperationMode.AUTO:
            return HVACMode.HEAT_COOL
        elif self._last_device_status.operation_mode == OperationMode.DRY:
            return HVACMode.DRY
        elif self._last_device_status.operation_mode == OperationMode.FAN:
            return HVACMode.FAN_ONLY
        elif self._last_device_status.operation_mode == OperationMode.NANOE:
            return HVACMode.FAN_ONLY
        else:
            return HVACMode.OFF

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return available HVAC modes."""
        return [
            HVACMode.OFF,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.HEAT_COOL,
            HVACMode.DRY,
            HVACMode.FAN_ONLY,
        ]

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        _LOGGER.debug(f"[{self._appliance.nickname}] current_temperature()")
        return self._last_device_status.inside_temp

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._last_device_status.temperature

    @property
    def fan_modes(self) -> list[str]:
        """Return available fan modes."""
        return ["Auto", "Quiet", "Low", "Medium", "Medium High", "High", "Very High", "Max"]

    @property
    def fan_mode(self) -> str:
        """Return current fan mode."""
        _LOGGER.debug(f"[{self._appliance.nickname}] fan_mode()")
        _LOGGER.debug(f"[{self._appliance.nickname}] current wind_volume {self._last_device_status.wind_volume}")
        _LOGGER.debug(f"[{self._appliance.nickname}] current air_flow {self._last_device_status.air_flow}")

        if self._last_device_status.wind_volume == WindVolume.LOW or self._last_device_status.wind_volume == WindVolume.MEDIUM:
            return "Low"
        elif self._last_device_status.wind_volume == WindVolume.MEDIUM_HIGH:
            return "Medium"
        elif self._last_device_status.wind_volume == WindVolume.HIGH:
            return "High"
        elif self._last_device_status.wind_volume == WindVolume.VERY_HIGH:
            return "Very High"
        else:
            if self._last_device_status.air_flow == AirFlow.QUIET:
                return "Quiet"
            elif self._last_device_status.air_flow == AirFlow.POWERFUL:
                return "Max"
            else:
                return "Auto"

    @property
    def swing_modes(self) -> list[str]:
        """Return available swing modes."""
        return ["Auto", "Top", "Middle Top", "Middle", "Middle Bottom", "Bottom", "Auto", "Swing"]

    @property
    def swing_mode(self) -> str:
        """Return current swing mode."""
        _LOGGER.debug(f"[{self._appliance.nickname}] swing_modes()")
        _LOGGER.debug(f"[{self._appliance.nickname}] current swing_mode {self._last_device_status.wind_direction}")
        if self._last_device_status.wind_direction == WindDirection.AUTO:
            return "Auto"
        if self._last_device_status.wind_direction == WindDirection.TOP:
            return "Top"
        elif self._last_device_status.wind_direction == WindDirection.MIDDLE_TOP:
            return "Middle Top"
        elif self._last_device_status.wind_direction == WindDirection.MIDDLE:
            return "Middle"
        elif self._last_device_status.wind_direction == WindDirection.MIDDLE_BOTTOM:
            return "Middle Bottom"
        elif self._last_device_status.wind_direction == WindDirection.BOTTOM:
            return "Bottom"
        elif self._last_device_status.wind_direction == WindDirection.SWING:
            return "Swing"
        else:
            return "Auto"


    @property
    def preset_modes(self) -> list[str]:
        return [PRESET_NONE, PRESET_SLEEP, PRESET_BOOST]

    @property
    def preset_mode(self) -> str:
        if self._last_device_status.air_flow == AirFlow.QUIET:
            return PRESET_SLEEP
        elif self._last_device_status.air_flow == AirFlow.POWERFUL:
            return PRESET_BOOST
        else:
            return PRESET_NONE


    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            _LOGGER.debug(f"Set temperature to {temperature}")
            try:
                await self._coordinator._async_set_temperature(temperature)
                await self._coordinator.async_request_refresh()
            except DeviceLockedByAnotherControllerException:
                _LOGGER.error(f"Cannot change {self._appliance.nickname} - it's being controlled by another device")
                raise HomeAssistantError(
                    f"{self._appliance.nickname} is being controlled by another device. "
                    "Please wait 2 minutes before trying again."
                )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        _LOGGER.debug(f"Set HVAC mode to {hvac_mode}")

        try:
            if hvac_mode == HVACMode.OFF:
                # Turn off the AC
                await self._coordinator._async_set_off()
            else:
                # Map the HVAC mode to operation mode
                operation_mode = HVAC_MODE_MAP_REVERSE.get(hvac_mode)
                if operation_mode:
                    await self._coordinator._async_set_hvac_mode(operation_mode, True)
                else:
                    _LOGGER.error(f"Unknown HVAC mode: {hvac_mode}")
                    return

            await self._coordinator.async_request_refresh()
        except DeviceLockedByAnotherControllerException:
            _LOGGER.error(f"Cannot change {self._appliance.nickname} - it's being controlled by another device")
            raise HomeAssistantError(
                f"{self._appliance.nickname} is being controlled by another device. "
                "Please wait 2 minutes before trying again."
            )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        _LOGGER.debug(f"Set fan mode to {fan_mode}")

        try:
            # Check if it's a special air flow mode
            if fan_mode in FAN_MODE_TO_AIR_FLOW:
                air_flow = FAN_MODE_TO_AIR_FLOW[fan_mode]
                await self._coordinator._async_set_fan_mode(wind_volume=None, air_flow=air_flow)
            elif fan_mode in FAN_MODE_TO_WIND_VOLUME:
                wind_volume = FAN_MODE_TO_WIND_VOLUME[fan_mode]
                # Reset air_flow to not_set when setting wind volume
                await self._coordinator._async_set_fan_mode(wind_volume=wind_volume, air_flow="not_set")
            else:
                _LOGGER.error(f"Unknown fan mode: {fan_mode}")
                return

            await self._coordinator.async_request_refresh()
        except DeviceLockedByAnotherControllerException:
            _LOGGER.error(f"Cannot change {self._appliance.nickname} - it's being controlled by another device")
            raise HomeAssistantError(
                f"{self._appliance.nickname} is being controlled by another device. "
                "Please wait 2 minutes before trying again."
            )

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new swing mode."""
        _LOGGER.debug(f"Set swing mode to {swing_mode}")

        try:
            wind_direction = SWING_MODE_TO_WIND_DIRECTION.get(swing_mode)
            if wind_direction is not None:
                await self._coordinator._async_set_swing_mode(wind_direction)
            else:
                _LOGGER.error(f"Unknown swing mode: {swing_mode}")
                return

            await self._coordinator.async_request_refresh()
        except DeviceLockedByAnotherControllerException:
            _LOGGER.error(f"Cannot change {self._appliance.nickname} - it's being controlled by another device")
            raise HomeAssistantError(
                f"{self._appliance.nickname} is being controlled by another device. "
                "Please wait 2 minutes before trying again."
            )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _LOGGER.debug(f"Set preset mode to {preset_mode}")

        try:
            air_flow = PRESET_MODE_TO_AIR_FLOW.get(preset_mode)
            if air_flow is not None:
                await self._coordinator._async_set_preset_mode(air_flow)
            else:
                _LOGGER.error(f"Unknown preset mode: {preset_mode}")
                return

            await self._coordinator.async_request_refresh()
        except DeviceLockedByAnotherControllerException:
            _LOGGER.error(f"Cannot change {self._appliance.nickname} - it's being controlled by another device")
            raise HomeAssistantError(
                f"{self._appliance.nickname} is being controlled by another device. "
                "Please wait 2 minutes before trying again."
            )
