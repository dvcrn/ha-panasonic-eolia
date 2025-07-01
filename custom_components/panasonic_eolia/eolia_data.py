from attr import dataclass

from custom_components.panasonic_eolia.eolia.auth import PanasonicEolia


@dataclass
class EoliaData:
    eolia: PanasonicEolia
