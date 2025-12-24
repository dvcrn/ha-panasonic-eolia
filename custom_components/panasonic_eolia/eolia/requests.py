class UpdateDeviceRequest:
    def __init__(
        self,
        nanoex=None,
        operation_status=None,
        airquality=None,
        wind_volume=None,
        temperature=None,
        operation_mode=None,
        wind_direction=None,
        timer_value=None,
        operation_token=None,
        wind_direction_horizon=None,
        air_flow=None,
    ):
        self.nanoex = nanoex
        self.operation_status = operation_status
        self.airquality = airquality
        self.wind_volume = wind_volume
        self.temperature = temperature
        self.operation_mode = operation_mode
        self.wind_direction = wind_direction
        self.timer_value = timer_value
        self.operation_token = operation_token
        self.wind_direction_horizon = wind_direction_horizon
        self.air_flow = air_flow

    @classmethod
    def from_dict(cls, data):
        return cls(
            nanoex=data.get("nanoex"),
            operation_status=data.get("operation_status"),
            airquality=data.get("airquality"),
            wind_volume=data.get("wind_volume"),
            temperature=data.get("temperature"),
            operation_mode=data.get("operation_mode"),
            wind_direction=data.get("wind_direction"),
            timer_value=data.get("timer_value"),
            operation_token=data.get("operation_token"),
            wind_direction_horizon=data.get("wind_direction_horizon"),
            air_flow=data.get("air_flow"),
        )

    def to_dict(self):
        return {
            "nanoex": self.nanoex,
            "operation_status": self.operation_status,
            "airquality": self.airquality,
            "wind_volume": self.wind_volume,
            "temperature": self.temperature,
            "operation_mode": self.operation_mode,
            "wind_direction": self.wind_direction,
            "timer_value": self.timer_value,
            "operation_token": self.operation_token,
            "wind_direction_horizon": self.wind_direction_horizon,
            "air_flow": self.air_flow,
        }
