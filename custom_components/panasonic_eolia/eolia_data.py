from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from custom_components.panasonic_eolia.eolia.auth import PanasonicEolia
from custom_components.panasonic_eolia.eolia.device import Appliance

type PanasonicEoliaConfigEntry = ConfigEntry[EoliaData]

@dataclass
class EoliaData:
    eolia: PanasonicEolia
    appliances: list[Appliance]
