# single file of aio-mc-rcon
# https://github.com/Iapetus-11/aio-mc-rcon
"""
MIT License

Copyright (c) 2020-2022 Milo Weinberg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import asyncio
import random
import struct
import enum
from typing import Any

from helper.errors import (
    ClientNotConnectedError,
    IncorrectPasswordError,
    RCONConnectionError,
)


class MessageType(enum.IntEnum):
    LOGIN = 3
    COMMAND = 2
    RESPONSE = 0
    INVALID_AUTH = -1


class RconClient:
    """The base class for creating an RCON client."""

    def __init__(self, host: str, port: int, password: str) -> None:
        self.host = host
        self.port = port
        self.password = password

        self._reader = None
        self._writer = None

        self._ready = False

    async def __aenter__(self, timeout=2) -> RconClient:
        return await self.connect(timeout)

    async def __aexit__(self, exc_type: type, exc: Exception, tb: Any) -> None:
        await self.close()

    async def connect(self, timeout: float = 2.0):
        """Sets up the connection between the client and server."""

        if self._ready:
            return

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout
            )
        except (asyncio.TimeoutError, TimeoutError) as e:
            raise RCONConnectionError(
                "A timeout occurred whilst attempting to connect to the server.", e
            )
        except ConnectionRefusedError as e:
            raise RCONConnectionError("The remote server refused the connection.", e)
        except Exception as e:
            raise RCONConnectionError("The connection failed for an unknown reason.", e)

        await self._send_msg(MessageType.LOGIN, self.password)

        self._ready = True
        return self

    async def _send_msg(self, type_: int, msg: str) -> tuple[str, str, int]:
        """Sends data to the server, and returns the response."""

        # randomly generate request id
        req_id = random.randint(0, 2147483647)

        # pack request id, packet type, and the actual message
        packet_data = (
            struct.pack("<ii", req_id, type_) + msg.encode("utf8") + b"\x00\x00"
        )

        # pack length of packet + rest of packet data
        packet = struct.pack("<i", len(packet_data)) + packet_data

        # send the data to the server
        self._writer.write(packet)
        await self._writer.drain()

        # read + unpack length of incoming packet
        in_len = struct.unpack("<i", (await self._reader.read(4)))[0]

        # read rest of packet data
        in_arr = []
        in_tlen = 0

        while in_tlen < in_len:
            in_tmp = await self._reader.read(in_len - in_tlen)

            if not in_tmp:
                break

            in_tlen += len(in_tmp)
            in_arr.append(in_tmp)

        in_data = b"".join(in_arr)

        if len(in_data) != in_len or not in_data.endswith(b"\x00\x00"):
            raise ValueError("Invalid data received from server.")

        # decode the incoming request id and packet type
        recType, in_req_id = struct.unpack("<ii", in_data[0:8])

        if recType == MessageType.INVALID_AUTH:
            raise IncorrectPasswordError

        # decode the received message
        recMsg = in_data[8:-2].decode("utf8")

        return recMsg, msg, recType

    async def send_cmd(self, cmd: str, timeout: float = 2.0) -> tuple[str, str, int]:
        """Sends a command to the server."""

        if not self._ready:
            raise ClientNotConnectedError

        return await asyncio.wait_for(self._send_msg(MessageType.COMMAND, cmd), timeout)

    async def close(self) -> None:
        """Closes the connection between the client and the server."""

        if self._ready:
            self._writer.close()
            await self._writer.wait_closed()

            self._reader = None
            self._writer = None

            self._ready = False
