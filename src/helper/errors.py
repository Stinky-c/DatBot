class CogLoadingFailure(Exception):
    """For when you just refuse to load the cog"""


class ClientNotConnectedError(Exception):
    pass


class IncorrectPasswordError(Exception):
    pass


class RCONConnectionError(Exception):
    pass
