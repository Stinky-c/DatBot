from typing import Optional


class CogLoadingFailure(Exception):
    """For when you just refuse to load the cog"""


class ClientNotConnectedError(Exception):
    pass


class IncorrectPasswordError(Exception):
    pass


class RCONConnectionError(Exception):
    pass


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
