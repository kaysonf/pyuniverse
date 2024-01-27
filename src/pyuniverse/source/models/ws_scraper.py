import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable, Union

from websockets import WebSocketClientProtocol, connect


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


class WsScraper:
    def __init__(
        self,
        create_ws: Callable[[], connect],
        on_msg: Callable[[Any], None],
    ):
        self.__state: TaskState = Ready()
        self.__create_connection = create_ws
        self.__on_msg = on_msg

        self.__user_event_queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=5)

    @property
    def state(self) -> TaskState:
        return self.__state

    def stop(self):
        self.__user_event_queue.put_nowait(ShutdownEvent())

    def send(self, msg: str):
        self.__user_event_queue.put_nowait(SendMessageEvent(msg))

    async def start(self, message: str, running_meta: str):
        if isinstance(self.__state, (Loading, Running)):
            return

        async with self.__ws_connection() as websocket:  # type: WebSocketClientProtocol

            async def wait_for_recv_message_event() -> ReceiveMessageEvent:
                res = await websocket.recv()
                return ReceiveMessageEvent(res)

            async def wait_for_user_events() -> Event:
                return await self.__user_event_queue.get()

            await websocket.send(message)

            while websocket.open:
                if not isinstance(self.__state, Running):
                    self.__state = Running(running_meta)

                tasks = [
                    asyncio.create_task(wait_for_recv_message_event()),
                    asyncio.create_task(wait_for_user_events()),
                ]

                done_first, pending = await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_COMPLETED
                )

                try:
                    for coro in done_first:
                        event = coro.result()

                        if isinstance(event, ReceiveMessageEvent):
                            self.__on_msg(event.data)

                        if isinstance(event, ShutdownEvent):
                            await websocket.close()

                        if isinstance(event, SendMessageEvent):
                            await websocket.send(event.msg)

                finally:  # TODO think again
                    for p in pending:
                        p.cancel()

    @asynccontextmanager
    async def __ws_connection(
        self,
    ) -> AsyncGenerator[WebSocketClientProtocol, Any]:
        self.__state = Loading()

        try:
            async with self.__create_connection() as ws:
                yield ws

        except Exception as e:
            print(e)
            self.__state = Error(str(e))

        finally:
            print("ws closed")  # TODO log
            if not isinstance(self.__state, Error):
                self.__state = Ready()
