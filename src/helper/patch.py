from logging import Logger
from typing import Callable


def patch_wavelink_loggers(func: Callable[[str], Logger], base: str):
    import wavelink.player
    import wavelink.pool
    import wavelink.websocket

    wavelink.player.logger = func(base + "player")
    wavelink.websocket.logger = func(base + "websocket")
    wavelink.pool.logger = func(base + "pool")
