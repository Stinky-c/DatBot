from typing import Callable
from logging import Logger


def patch_wavelink_loggers(func: Callable[[str], Logger], base: str):
    import wavelink.websocket
    import wavelink.player
    import wavelink.pool

    wavelink.player.logger = func(base + "player")
    wavelink.websocket.logger = func(base + "websocket")
    wavelink.pool.logger = func(base + "pool")
