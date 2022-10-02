class DeviceException(Exception):
    """Exception wrapping any communication errors with the device."""


class DeviceUpdateFailedException(DeviceException):
    """ """


class InvalidValueException(ValueError):
    """ """


class InvalidActionException(ValueError):
    """ """
