import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

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
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Panasonic Eolia climate platform."""
    _LOGGER.debug("Climate async_setup_entry called")

    # For now, create a dummy entity
    # Later this will use the coordinator from hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PanasonicEoliaClimate()])


class PanasonicEoliaClimate(ClimateEntity):
    """Representation of a Panasonic Eolia climate device."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
    )

    def __init__(self) -> None:
        """Initialize the climate device."""
        _LOGGER.debug("Climate entity init called")
        super().__init__()

        # Temporary hardcoded values
        self._attr_unique_id = "panasonic_eolia_test"
        self._attr_name = "Test AC"

        # State variables
        self._current_temperature = 25.0
        self._target_temperature = 22.0
        self._hvac_mode = HVACMode.OFF
        self._is_on = False

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if not self._is_on:
            return HVACMode.OFF
        return self._hvac_mode

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
        return self._current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def fan_modes(self) -> list[str]:
        """Return available fan modes."""
        return ["Auto", "Low", "Medium", "High"]

    @property
    def fan_mode(self) -> str:
        """Return current fan mode."""
        return "Auto"

    @property
    def swing_modes(self) -> list[str]:
        """Return available swing modes."""
        return ["Off", "Vertical", "Horizontal", "Both"]

    @property
    def swing_mode(self) -> str:
        """Return current swing mode."""
        return "Off"

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
