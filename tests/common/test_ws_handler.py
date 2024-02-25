import asyncio
from typing import List

import pytest
import websockets

from pyuniverse.common.ws_handler import (
    Ready,
    SendMessageEvent,
    ShutdownEvent,
    WsHandler,
)


def test_ws_handler_initial_state():
    handler = WsHandler()
    assert isinstance(handler.state, Ready) is True


@pytest.mark.asyncio
async def test_receive_messages(next_available_local_port):
    handler = WsHandler()
    all_msgs_recv = asyncio.Event()

    first_message = "first_message"
    second_message = "second_message"

    messages: List[str] = []

    to_send = [first_message, second_message]

    async def server(websocket: websockets.WebSocketServerProtocol):
        for msg in to_send:
            await websocket.send(msg)

        await asyncio.wait_for(all_msgs_recv.wait(), timeout=3)

    def on_msg_recv(msg: str):
        messages.append(msg)
        if len(messages) == len(to_send):
            all_msgs_recv.set()

    async with websockets.serve(server, "localhost", next_available_local_port):
        async with websockets.connect(
            f"ws://localhost:{next_available_local_port}"
        ) as ws_client:
            await handler.run(ws_client=ws_client, on_msg=on_msg_recv)

    assert [first_message, second_message] == messages


@pytest.mark.asyncio
async def test_shutdown(next_available_local_port):
    handler = WsHandler()
    all_msgs_recv = asyncio.Event()

    first_message = "first_message"
    second_message = "second_message"

    to_send = [first_message, second_message]

    async def server(websocket: websockets.WebSocketServerProtocol):
        for msg in to_send:
            await websocket.send(msg)

        await asyncio.wait_for(all_msgs_recv.wait(), timeout=3)
        await handler.add_to_queue(ShutdownEvent())

        await websocket.send("third message. I am not received by client")

    messages: List[str] = []

    def on_msg_recv(msg: str):
        messages.append(msg)
        if len(messages) == len(to_send):
            all_msgs_recv.set()

    async with websockets.serve(server, "localhost", next_available_local_port):
        async with websockets.connect(
            f"ws://localhost:{next_available_local_port}"
        ) as ws_client:
            await handler.run(ws_client=ws_client, on_msg=on_msg_recv)

    assert [first_message, second_message] == messages


@pytest.mark.asyncio
async def test_send(next_available_local_port):
    handler = WsHandler()

    first_message_to_send = "1"
    second_message_to_send = "2"

    async def server(websocket: websockets.WebSocketServerProtocol):
        res1 = await asyncio.wait_for(websocket.recv(), timeout=3)

        assert res1 == first_message_to_send

        res2 = await asyncio.wait_for(websocket.recv(), timeout=3)
        assert res2 == second_message_to_send

    async def send_message_from_client():
        await handler.add_to_queue(SendMessageEvent(first_message_to_send))
        await handler.add_to_queue(SendMessageEvent(second_message_to_send))

    async with websockets.serve(server, "localhost", next_available_local_port):
        async with websockets.connect(
            f"ws://localhost:{next_available_local_port}"
        ) as ws_client:
            await handler.run(
                ws_client=ws_client,
                on_msg=print,
                on_open_async=send_message_from_client,
            )
