class DeviceException(Exception):
    translation_key = None
    translation_placeholders = None
    translation_source = None
    localize = None

    def __str__(self):
        message = super().__str__()
        if self.translation_key and message == self.translation_key:
            localized = (
                DeviceException.localize(f"exceptions.{self.translation_key}.message")
                if DeviceException.localize
                else None
            )
            message = localized or self.translation_key.replace("_", " ").capitalize()
            for name, value in (self.translation_placeholders or {}).items():
                message = message.replace("{" + name + "}", str(value))
        return message

    def __init__(self, *args, key=None, source=None, **placeholders):
        cause = args[0] if args and isinstance(args[0], DeviceException) else None
        self.translation_key = key or self.translation_key or (cause.translation_key if cause is not None else None)
        self.translation_source = source or (cause.translation_source if cause is not None else None)
        if cause is not None and not placeholders:
            placeholders = cause.translation_placeholders or {}
        super().__init__(*(args if args or self.translation_key is None else (self.translation_key,)))
        self.translation_placeholders = {k: str(v) for k, v in placeholders.items()} or None


class InvalidActionException(DeviceException, ValueError):
    """ """


class DeviceUnavailableException(InvalidActionException):
    translation_key = "device_unavailable"


class CommandFailedException(InvalidActionException):
    translation_key = "command_failed"


class EntityUnavailableException(DeviceException):
    translation_key = "entity_unavailable"


class NotSupportedException(InvalidActionException):
    translation_key = "not_supported"


class MapSelectFailedException(InvalidActionException):
    translation_key = "map_select_failed"


class NotFoundException(InvalidActionException):
    translation_key = "not_found"


class UnavailableException(InvalidActionException):
    translation_key = "unavailable"


class MissingParameterException(InvalidActionException):
    translation_key = "missing_parameter"
