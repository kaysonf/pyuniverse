import json
import ssl
from typing import List

import certifi
import websockets

from pyuniverse.common.ws_scraper import Error, Ready, Running, WsScraper

from .models import DeribitOperation, DeribitUpdate


def write_to_file(response):
    res: dict = json.loads(response)
    params = res.get("params")
    if params:
        print(params.get("channel"))
    # with open("output.jsonl", "a") as outfile:
    #     outfile.write(response)
    #     outfile.write("\n")


deribit_scraper = WsScraper(
    lambda: websockets.connect(
        "wss://www.deribit.com/ws/api/v2",
        ssl=ssl.create_default_context(cafile=certifi.where()),
    ),
    on_msg=write_to_file,
)


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


async def start(ws: WsScraper, channels: List[str]):
    if isinstance(ws.state, (Ready, Error)):
        msg = create_msg(DeribitOperation.subscribe.value, channels)
        await ws.start(msg, "")


def update(ws: WsScraper, deribit_update: List[DeribitUpdate]):
    if not isinstance(ws.state, Running):
        return f"not running - {ws.state}"

    def send(operation: DeribitOperation):
        channels = [op.channel for op in deribit_update if op.operation == operation]
        if channels:
            msg = create_msg(operation.value, channels)
            ws.send(msg)

    send(DeribitOperation.subscribe)
    send(DeribitOperation.unsubscribe)

    return str(ws.state)
