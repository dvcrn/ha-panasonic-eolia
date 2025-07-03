"""Exceptions for Panasonic Eolia integration."""

class PanasonicEoliaException(Exception):
    """Base exception for Panasonic Eolia."""
    pass


class DeviceLockedByAnotherControllerException(PanasonicEoliaException):
    """Exception raised when device is locked by another controller."""
    
    def __init__(self, message="Device is locked by another controller. Please wait 2 minutes before trying again."):
        self.message = message
        super().__init__(self.message)