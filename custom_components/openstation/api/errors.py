"""Errors raised by the OpenStation API layer."""


class OpenStationError(Exception):
    """Base class for OpenStation errors."""


class OpenStationConnectionError(OpenStationError):
    """A feed could not be fetched."""


class OpenStationParseError(OpenStationError):
    """A feed was fetched but its content is unusable."""
