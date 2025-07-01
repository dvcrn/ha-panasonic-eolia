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
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.panasonic_eolia.eolia.auth import PanasonicEolia
from custom_components.panasonic_eolia.eolia.device import Appliance
from custom_components.panasonic_eolia.eolia.responses import (
    AirFlow,
    DeviceStatus,
    OperationMode,
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
    "Dry": HVACMode.DRY,
    "Fan": HVACMode.FAN_ONLY,
}

HVAC_MODE_MAP_REVERSE = {v: k for k, v in HVAC_MODE_MAP.items()}


async def async_setup_entry(
    hass: HomeAssistant, entry: PanasonicEoliaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Panasonic Eolia climate platform."""
    _LOGGER.debug(dir(entry.runtime_data))
    _LOGGER.debug(entry.runtime_data)

    _LOGGER.debug(f"Climate async_setup_entry called, num devices: {len(entry.runtime_data.appliances)}")


    entities = []
    for device in entry.runtime_data.appliances:
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

    def __init__(self, coordinator: EolliaApplianceDataCoordinator, appliance: Appliance, eolia: PanasonicEolia) -> None:
        """Initialize the climate device."""
        _LOGGER.debug(f"Climate entity init called with appliance: {appliance.nickname}")
        super().__init__(coordinator=coordinator)

        # Temporary hardcoded values
        self._attr_unique_id = appliance.appliance_id
        self._attr_name = appliance.nickname

        self._eolia = eolia
        self._appliance = appliance


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
        return ["Off", "Vertical", "Horizontal", "Both"]

    @property
    def swing_mode(self) -> str:
        """Return current swing mode."""
        _LOGGER.debug(f"[{self._appliance.nickname}] swing_modes()")
        _LOGGER.debug(f"[{self._appliance.nickname}] current swing_mode {self._last_device_status.wind_direction}")
        return "Off"


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
            self._target_temperature = temperature
            _LOGGER.debug(f"Set temperature to {temperature}")
            # TODO: Call API to update temperature

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        _LOGGER.debug(f"Set HVAC mode to {hvac_mode}")
        if hvac_mode == HVACMode.OFF:
            self._is_on = False
        else:
            self._is_on = True
            self._hvac_mode = hvac_mode
        # TODO: Call API to update mode

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        _LOGGER.debug(f"Set fan mode to {fan_mode}")
        # TODO: Call API to update fan mode

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new swing mode."""
        _LOGGER.debug(f"Set swing mode to {swing_mode}")
        # TODO: Call API to update swing mode
