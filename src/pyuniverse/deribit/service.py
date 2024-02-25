import json
import ssl
from typing import List

import certifi
import websockets

from pyuniverse.common.result import Err, Ok, Result
from pyuniverse.common.ws_handler import (
    Error,
    Ready,
    Running,
    SendMessageEvent,
    ShutdownEvent,
    WsHandler,
)

from .models import DeribitOperation, DeribitUpdate


def write_to_file(response):
    with open("output.jsonl", "a") as outfile:
        outfile.write(response)
        outfile.write("\n")


deribit_scraper = WsHandler()


class NextId:
    def __init__(self):
        self.__id = 0

    def __call__(self):
        self.__id += 1
        return self.__id


next_id = NextId()


def create_msg(method: str, channels: List[str]):
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": next_id(),
            "method": method,
            "params": {"channels": channels},
        }
    )


async def start(ws: WsHandler, channels: List[str]):
    if isinstance(ws.state, (Ready, Error)):
        async with websockets.connect(
            "wss://www.deribit.com/ws/api/v2",
            ssl=ssl.create_default_context(cafile=certifi.where()),
        ) as ws_client:

            async def send_subscription():
                msg = create_msg(DeribitOperation.subscribe.value, channels)
                await ws.add_to_queue(SendMessageEvent(msg))

            await ws.run(
                ws_client=ws_client,
                on_msg=write_to_file,
                on_open_async=send_subscription,
            )


async def stop(ws: WsHandler):
    await ws.add_to_queue(ShutdownEvent())


async def update(
    ws: WsHandler, deribit_update: List[DeribitUpdate]
) -> Result[str, str]:
    if not isinstance(ws.state, Running):
        return Err(f"not running - {ws.state}")

    async def send(operation: DeribitOperation):
        channels = [op.channel for op in deribit_update if op.operation == operation]
        if channels:
            msg = create_msg(operation.value, channels)
            await ws.add_to_queue(SendMessageEvent(msg))

    await send(DeribitOperation.subscribe)
    await send(DeribitOperation.unsubscribe)

    return Ok(f"{ws.state}")
