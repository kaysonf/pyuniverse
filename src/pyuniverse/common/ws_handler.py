import asyncio
from typing import Any, Callable, Coroutine, Union

from websockets import ConnectionClosedOK, WebSocketClientProtocol


class Loading:
    def __str__(self):
        return "LOADING"


class Running:
    def __init__(self, meta):
        self.meta = meta

    def __str__(self):
        return "RUNNING"


class Ready:
    def __str__(self):
        return "READY"


class Error:
    def __init__(self, reason: str):
        self.reason = reason

    def __str__(self):
        return f"ERROR - {self.reason}"


TaskState = Union[Loading, Running, Ready, Error]


class ReceiveMessageEvent:
    def __init__(self, data):
        self.data = data


class ShutdownEvent:
    pass


class SendMessageEvent:
    def __init__(self, msg: str):
        self.msg = msg


Event = ReceiveMessageEvent | ShutdownEvent | SendMessageEvent


class WsHandler:
    def __init__(self):
        self.__state: TaskState = Ready()
        self.__queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=5)

    @property
    def state(self) -> TaskState:
        return self.__state

    async def run(
        self,
        *,
        ws_client: WebSocketClientProtocol,
        on_msg: Callable[[Any], None],
        on_open_async: Callable[[], Coroutine[Any, Any, None]] | None = None,
    ):
        async def wait_for_user_events():
            return await self.__queue.get()

        async def wait_for_recv_message_event():
            res = await ws_client.recv()
            return ReceiveMessageEvent(res)

        while ws_client.open:
            if not isinstance(self.__state, Running):
                self.__state = Running("running")

                if on_open_async:
                    await on_open_async()

            tasks = [
                asyncio.create_task(
                    wait_for_recv_message_event(), name="wait_for_recv_message_event"
                ),
                asyncio.create_task(
                    wait_for_user_events(), name="wait_for_user_events"
                ),
            ]

            done_first, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )

            try:
                for coro in done_first:
                    event = coro.result()

                    if isinstance(event, ShutdownEvent):
                        await ws_client.close()
                        self.__state = Ready()

                    if isinstance(event, ReceiveMessageEvent):
                        on_msg(event.data)

                    if isinstance(event, SendMessageEvent):
                        await ws_client.send(event.msg)

            except ConnectionClosedOK:
                self.__state = Ready()

            except Exception as e:
                self.__state = Error(str(e))
                raise e

            finally:
                for p in pending:
                    p.cancel()

    async def add_to_queue(self, event: Event):
        await self.__queue.put(event)
