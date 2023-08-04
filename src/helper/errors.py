from typing import Optional

from disnake.ext.commands.errors import ExtensionError
from pydantic.error_wrappers import ValidationError

# Bot errors


class CogLoadingFailure(Exception):
    """For when you just refuse to load the cog"""


class MissingCogMeta(ExtensionError):
    """An exception raised when an extension does not have a ``metadata`` entry point function."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Extension {name!r} has no 'metadata' function.", name=name)


class ImproperConfiguration(Exception):
    """A improper Bot configuation is preventing startup"""

    def __init__(self, message: str, error: ValidationError) -> None:
        self.message = message
        self.error = error


# RCON errors


class ClientNotConnectedError(Exception):
    pass


class IncorrectPasswordError(Exception):
    pass


class RCONConnectionError(Exception):
    pass


# Math errors


class MathError(Exception):
    """General Math Error"""

    def __init__(self, statement: Optional[str] = None) -> None:
        self.statment = statement


class InvalidStatment(MathError):
    """Incorrectly formatted statment"""


class NotAFunction(MathError):
    """The statment contains an unknown functions"""


class NotAName(MathError):
    """Statement contains unknown symbols"""


class UnknownNode(MathError):
    """Statement contains unknown nodes"""
