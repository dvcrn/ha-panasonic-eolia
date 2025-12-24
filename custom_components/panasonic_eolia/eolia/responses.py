from enum import Enum
from typing import Optional, Union, cast

from .device import Appliance
from .requests import UpdateDeviceRequest


class OperationMode(Enum):
    OFF = "Off"
    STOP = "Stop"  # Added based on sample data
    COOLING = "Cooling"
    HEATING = "Heating"
    AUTO = "Auto"
    DRY = "CoolDehumidifying"
    FAN = "Blast"
    NANOE = "Nanoe"


class AirQualityName(Enum):
    OFF = "off"
    ON = "on"


class AIControl(Enum):
    OFF = "off"
    ON = "on"


class AirFlow(Enum):
    NOT_SET = "not_set"
    QUIET = "quiet"
    POWERFUL = "powerful"


class WindShieldHit(Enum):
    NOT_SET = "not_set"
    ON = "on"
    OFF = "off"


class WindDirectionHorizon(Enum):
    AUTO = "auto"
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    LEFT_CENTER = "left_center"
    CENTER_RIGHT = "center_right"
    WIDE = "wide"


class WindDirection(Enum):
    AUTO = 0
    TOP = 1
    MIDDLE_TOP = 2
    MIDDLE = 3
    MIDDLE_BOTTOM = 4
    BOTTOM = 5
    SWING = 6


class WindVolume(Enum):
    AUTO = 0  # when "silent" or "powerful" mode are set, this is set to 0, aka auto
    LOW = 1
    MEDIUM = 2
    MEDIUM_HIGH = 3
    HIGH = 4
    VERY_HIGH = 5


class DevicesResponse:
    def __init__(self, ac_list=None):
        self.ac_list = ac_list or []

    @classmethod
    def from_dict(cls, data):
        ac_list = []
        if "ac_list" in data:
            for item in data["ac_list"]:
                ac_list.append(Appliance.from_dict(item))
        return cls(ac_list=ac_list)

    def to_dict(self):
        return {"ac_list": [appliance.to_dict() for appliance in self.ac_list]}


class ProductFunctionsResponse:
    def __init__(
        self,
        ac_function_list=None,
        product_code=None,
        remote_controller_type=None,
        installation_type=None,
    ):
        self.ac_function_list = ac_function_list or []
        self.product_code = product_code
        self.remote_controller_type = remote_controller_type
        self.installation_type = installation_type

    @classmethod
    def from_dict(cls, data):
        ac_function_list = []
        if "ac_function_list" in data:
            for item in data["ac_function_list"]:
                ac_function_list.append(
                    {
                        "function_id": item.get("function_id"),
                        "function_value": item.get("function_value"),
                    }
                )
        return cls(
            ac_function_list=ac_function_list,
            product_code=data.get("product_code"),
            remote_controller_type=data.get("remote_controller_type"),
            installation_type=data.get("installation_type"),
        )

    def to_dict(self):
        return {
            "ac_function_list": self.ac_function_list,
            "product_code": self.product_code,
            "remote_controller_type": self.remote_controller_type,
            "installation_type": self.installation_type,
        }


class DeviceStatus:
    def __init__(self, **kwargs):
        # Define expected attributes with proper types
        self.appliance_id: Optional[str] = kwargs.get("appliance_id")
        self.operation_status: Optional[bool] = kwargs.get(
            "operation_status"
        )  # false = off, true = on

        # Convert operation_mode string to enum if provided
        self.operation_mode: Optional[Union[OperationMode, str]] = cast(
            Optional[Union[OperationMode, str]],
            self._parse_enum(kwargs.get("operation_mode"), OperationMode),
        )

        self.temperature: Optional[float] = kwargs.get(
            "temperature"
        )  # Target temperature
        # self.wind_volume: Optional[int] = kwargs.get('wind_volume')  # Fan speed level (e.g., 5)
        # self.wind_direction: Optional[int] = kwargs.get('wind_direction')  # Vertical direction (0 = 5)
        self.inside_humidity: Optional[int] = kwargs.get(
            "inside_humidity"
        )  # 999 = not available
        self.inside_temp: Optional[float] = kwargs.get(
            "inside_temp"
        )  # Current indoor temperature
        self.outside_temp: Optional[float] = kwargs.get(
            "outside_temp"
        )  # 999.0 = not available
        self.operation_priority: Optional[bool] = kwargs.get(
            "operation_priority"
        )  # false = normal
        self.timer_value: Optional[int] = kwargs.get(
            "timer_value"
        )  # Timer in minutes (0 = off)
        self.device_errstatus: Optional[bool] = kwargs.get(
            "device_errstatus"
        )  # false = no error
        self.airquality: Optional[bool] = kwargs.get(
            "airquality"
        )  # Air quality feature on/off
        self.nanoex: Optional[bool] = kwargs.get("nanoex")  # Nanoe-X feature on/off
        self.aq_value: Optional[int] = kwargs.get(
            "aq_value"
        )  # Air quality value (-1 = not available)

        # Parse enum fields
        self.wind_volume: Optional[Union[WindVolume, int]] = cast(
            Optional[Union[WindVolume, int]],
            self._parse_enum(kwargs.get("wind_volume"), WindVolume),
        )

        self.wind_direction: Optional[Union[WindDirection, str]] = cast(
            Optional[Union[WindDirection, str]],
            self._parse_enum(kwargs.get("wind_direction"), WindDirection),
        )

        self.aq_name: Optional[Union[AirQualityName, str]] = cast(
            Optional[Union[AirQualityName, str]],
            self._parse_enum(kwargs.get("aq_name"), AirQualityName),
        )
        self.ai_control: Optional[Union[AIControl, str]] = cast(
            Optional[Union[AIControl, str]],
            self._parse_enum(kwargs.get("ai_control"), AIControl),
        )
        self.air_flow: Optional[Union[AirFlow, str]] = cast(
            Optional[Union[AirFlow, str]],
            self._parse_enum(kwargs.get("air_flow"), AirFlow),
        )
        self.wind_shield_hit: Optional[Union[WindShieldHit, str]] = cast(
            Optional[Union[WindShieldHit, str]],
            self._parse_enum(kwargs.get("wind_shield_hit"), WindShieldHit),
        )
        self.wind_direction_horizon: Optional[Union[WindDirectionHorizon, str]] = cast(
            Optional[Union[WindDirectionHorizon, str]],
            self._parse_enum(
                kwargs.get("wind_direction_horizon"), WindDirectionHorizon
            ),
        )

        self.operation_token: Optional[str] = kwargs.get("operation_token")

    def _parse_enum(
        self, value: Optional[str], enum_class
    ) -> Optional[Union[Enum, str]]:
        """Helper to parse string value to enum, keeping raw value if no match"""
        if value is None:
            return None

        for enum_member in enum_class:
            if enum_member.value == value:
                return enum_member

        # If no match found, store the raw value
        return value

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        """Convert to dictionary, converting enums back to strings"""
        return {
            "appliance_id": self.appliance_id,
            "operation_status": self.operation_status,
            "operation_mode": self._enum_to_value(self.operation_mode),
            "temperature": self.temperature,
            "wind_volume": self.wind_volume,
            "wind_direction": self.wind_direction,
            "inside_humidity": self.inside_humidity,
            "inside_temp": self.inside_temp,
            "outside_temp": self.outside_temp,
            "operation_priority": self.operation_priority,
            "timer_value": self.timer_value,
            "device_errstatus": self.device_errstatus,
            "airquality": self.airquality,
            "nanoex": self.nanoex,
            "aq_value": self.aq_value,
            "aq_name": self._enum_to_value(self.aq_name),
            "ai_control": self._enum_to_value(self.ai_control),
            "air_flow": self._enum_to_value(self.air_flow),
            "wind_shield_hit": self._enum_to_value(self.wind_shield_hit),
            "wind_direction_horizon": self._enum_to_value(self.wind_direction_horizon),
            "operation_token": self.operation_token,
        }

    def _enum_to_value(self, value: Optional[Union[Enum, str]]) -> Optional[str]:
        """Convert enum to its string value, or return as-is if not enum"""
        if value is None:
            return None
        if isinstance(value, Enum):
            return value.value
        return value

    def to_update_request(self):
        """Convert DeviceStatus to UpdateDeviceRequest, filtering out read-only fields"""
        return UpdateDeviceRequest(
            nanoex=self.nanoex,
            operation_status=self.operation_status,
            airquality=self.airquality,
            wind_volume=self._enum_to_value(self.wind_volume),
            temperature=str(self.temperature) if self.temperature is not None else None,
            operation_mode=self._enum_to_value(self.operation_mode),
            wind_direction=self._enum_to_value(self.wind_direction),
            timer_value=str(self.timer_value) if self.timer_value is not None else None,
            operation_token=self.operation_token,
            wind_direction_horizon=self._enum_to_value(self.wind_direction_horizon),
        )
