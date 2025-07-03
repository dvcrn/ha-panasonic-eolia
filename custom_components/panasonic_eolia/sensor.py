"""Sensor platform for Panasonic Eolia integration."""
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.panasonic_eolia.eolia.auth import PanasonicEolia
from custom_components.panasonic_eolia.eolia.device import Appliance
from custom_components.panasonic_eolia.eolia.responses import DeviceStatus
from custom_components.panasonic_eolia.eolia_data import (
    EolliaApplianceDataCoordinator,
    PanasonicEoliaConfigEntry,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


async def async_setup_entry(
    hass: HomeAssistant, entry: PanasonicEoliaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Panasonic Eolia sensor platform."""
    _LOGGER.debug(f"Sensor async_setup_entry called, num devices: {len(entry.runtime_data.appliances)}")

    entities = []
    for device in entry.runtime_data.appliances:
        coordinator = EolliaApplianceDataCoordinator(hass, entry.runtime_data.eolia, device)

        entity = PanasonicEoliaTemperatureSensor(
            coordinator=coordinator,
            appliance=device,
            eolia=entry.runtime_data.eolia
        )
        entities.append(entity)

    async_add_entities(entities)


class PanasonicEoliaTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Panasonic Eolia temperature sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    _appliance: Appliance
    _eolia: PanasonicEolia
    _last_device_status: DeviceStatus
    _coordinator: EolliaApplianceDataCoordinator

    def __init__(self, coordinator: EolliaApplianceDataCoordinator, appliance: Appliance, eolia: PanasonicEolia) -> None:
        """Initialize the temperature sensor."""
        _LOGGER.debug(f"Temperature sensor init called with appliance: {appliance.nickname}")
        super().__init__(coordinator=coordinator)

        # Set unique ID and name
        self._attr_unique_id = f"{appliance.appliance_id}_temperature"
        self._attr_name = f"{appliance.nickname} Temperature"

        self._eolia = eolia
        self._appliance = appliance
        self._coordinator = coordinator

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(f"Temperature sensor handle_coordinator_update called for {self._appliance.nickname}")
        if self.coordinator.data:
            self._last_device_status = self.coordinator.data.status
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> float:
        """Return the current temperature value."""
        if self._coordinator and self._coordinator._appliance_status:
            if self._coordinator._appliance_status.inside_temp:
                return self._coordinator._appliance_status.inside_temp
        return 0
