from enum import Enum

from .device import Appliance
from .requests import UpdateDeviceRequest


class OperationMode(Enum):
    OFF = "Off"
    COOLING = "Cooling"
    HEATING = "Heating"
    AUTO = "Auto"
    DRY = "CoolDehumidifying"
    FAN = "Fan"


class DevicesResponse:
    def __init__(self, ac_list=None):
        self.ac_list = ac_list or []

    @classmethod
    def from_dict(cls, data):
        ac_list = []
        if 'ac_list' in data:
            for item in data['ac_list']:
                ac_list.append(Appliance.from_dict(item))
        return cls(ac_list=ac_list)

    def to_dict(self):
        return {
            'ac_list': [appliance.to_dict() for appliance in self.ac_list]
        }

class ProductFunctionsResponse:
    def __init__(self, ac_function_list=None, product_code=None, remote_controller_type=None, installation_type=None):
        self.ac_function_list = ac_function_list or []
        self.product_code = product_code
        self.remote_controller_type = remote_controller_type
        self.installation_type = installation_type

    @classmethod
    def from_dict(cls, data):
        ac_function_list = []
        if 'ac_function_list' in data:
            for item in data['ac_function_list']:
                ac_function_list.append({
                    'function_id': item.get('function_id'),
                    'function_value': item.get('function_value')
                })
        return cls(
            ac_function_list=ac_function_list,
            product_code=data.get('product_code'),
            remote_controller_type=data.get('remote_controller_type'),
            installation_type=data.get('installation_type')
        )

    def to_dict(self):
        return {
            'ac_function_list': self.ac_function_list,
            'product_code': self.product_code,
            'remote_controller_type': self.remote_controller_type,
            'installation_type': self.installation_type
        }

class DeviceStatus:
    def __init__(self, **kwargs):
        # Define expected attributes with default values
        self.appliance_id = kwargs.get('appliance_id')
        self.operation_status = kwargs.get('operation_status')

        # Convert operation_mode string to enum if provided
        operation_mode_value = kwargs.get('operation_mode')
        if operation_mode_value is not None:
            # Try to find matching enum value
            self.operation_mode = None
            for mode in OperationMode:
                if mode.value == operation_mode_value:
                    self.operation_mode = mode
                    break
            # If no match found, store the raw value
            if self.operation_mode is None:
                self.operation_mode = operation_mode_value
        else:
            self.operation_mode = None

        self.temperature = kwargs.get('temperature')
        self.wind_volume = kwargs.get('wind_volume')
        self.wind_direction = kwargs.get('wind_direction')
        self.inside_humidity = kwargs.get('inside_humidity')
        self.inside_temp = kwargs.get('inside_temp')
        self.outside_temp = kwargs.get('outside_temp')
        self.operation_priority = kwargs.get('operation_priority')
        self.timer_value = kwargs.get('timer_value')
        self.device_errstatus = kwargs.get('device_errstatus')
        self.airquality = kwargs.get('airquality')
        self.nanoex = kwargs.get('nanoex')
        self.aq_value = kwargs.get('aq_value')
        self.aq_name = kwargs.get('aq_name')
        self.ai_control = kwargs.get('ai_control')
        self.air_flow = kwargs.get('air_flow')
        self.wind_shield_hit = kwargs.get('wind_shield_hit')
        self.wind_direction_horizon = kwargs.get('wind_direction_horizon')
        self.operation_token = kwargs.get('operation_token')

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        # Include all keys to match API expectations
        return {
            'appliance_id': self.appliance_id,
            'operation_status': self.operation_status,
            'operation_mode': self.operation_mode.value if isinstance(self.operation_mode, OperationMode) else self.operation_mode,
            'temperature': self.temperature,
            'wind_volume': self.wind_volume,
            'wind_direction': self.wind_direction,
            'inside_humidity': self.inside_humidity,
            'inside_temp': self.inside_temp,
            'outside_temp': self.outside_temp,
            'operation_priority': self.operation_priority,
            'timer_value': self.timer_value,
            'device_errstatus': self.device_errstatus,
            'airquality': self.airquality,
            'nanoex': self.nanoex,
            'aq_value': self.aq_value,
            'aq_name': self.aq_name,
            'ai_control': self.ai_control,
            'air_flow': self.air_flow,
            'wind_shield_hit': self.wind_shield_hit,
            'wind_direction_horizon': self.wind_direction_horizon,
            'operation_token': self.operation_token
        }

    def to_update_request(self):
        """Convert DeviceStatus to UpdateDeviceRequest, filtering out read-only fields"""

        return UpdateDeviceRequest(
            nanoex=self.nanoex,
            operation_status=self.operation_status,
            airquality=self.airquality,
            wind_volume=self.wind_volume,
            temperature=str(self.temperature) if self.temperature is not None else None,
            operation_mode=self.operation_mode.value if isinstance(self.operation_mode, OperationMode) else self.operation_mode,
            wind_direction=self.wind_direction,
            timer_value=str(self.timer_value) if self.timer_value is not None else None,
            operation_token=self.operation_token,
            wind_direction_horizon=self.wind_direction_horizon
        )
