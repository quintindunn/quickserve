import asyncio
import logging
import threading

from collections.abc import Awaitable, Callable
from concurrent.futures import Future

import websockets

from websockets.asyncio.server import Server, ServerConnection

MessageHandler = Callable[[str, "SimpleController"], Awaitable[None]]
ConnectionHandler = Callable[["SimpleController"], Awaitable[None]]

PING_TIMEOUT = 120

logger = logging.getLogger(__name__)


class SimpleController:
    def __init__(self, host: str, port: int, loop: asyncio.AbstractEventLoop):
        self.host = host
        self.port = port
        self.loop = loop

        self.websocket: ServerConnection | None = None

        self._server: Server | None = None
        self._closed = asyncio.Event()
        self._ping_task: asyncio.Task[None] | None = None

        self._on_message_registry: list[MessageHandler] = []
        self._on_connect_registry: list[ConnectionHandler] = []
        self._on_close_registry: list[ConnectionHandler] = []

    def on_message(self) -> Callable[[MessageHandler], MessageHandler]:
        def decorator(func: MessageHandler) -> MessageHandler:
            self._on_message_registry.append(func)
            return func

        return decorator

    def on_connect(self) -> Callable[[ConnectionHandler], ConnectionHandler]:
        def decorator(func: ConnectionHandler) -> ConnectionHandler:
            self._on_connect_registry.append(func)
            return func

        return decorator

    def on_close(self) -> Callable[[ConnectionHandler], ConnectionHandler]:
        def decorator(func: ConnectionHandler) -> ConnectionHandler:
            self._on_close_registry.append(func)
            return func

        return decorator

    async def _handle_connection(
        self,
        websocket: ServerConnection,
    ) -> None:
        self.websocket = websocket
        self._reset_ping_timeout()

        try:
            await self._on_connect()

            async for message in websocket:
                await self._on_message(message)

        except websockets.ConnectionClosed:
            pass

        finally:
            self._cancel_ping_timeout()

            self.websocket = None
            await self._on_close()

    async def _on_message(self, message: str) -> None:
        if message == "simple-ping":
            self._reset_ping_timeout()
            return

        for handler in self._on_message_registry:
            await handler(message, self)

    def _reset_ping_timeout(self) -> None:
        self._cancel_ping_timeout()

        self._ping_task = asyncio.create_task(
            self._ping_timeout(),
        )

    def _cancel_ping_timeout(self) -> None:
        if self._ping_task is not None:
            self._ping_task.cancel()
            self._ping_task = None

    async def _ping_timeout(self) -> None:
        try:
            await asyncio.sleep(PING_TIMEOUT)

            logger.info(
                f"Controller on port {self.port} timed out",
            )

            await self.stop()

        except asyncio.CancelledError:
            pass

    async def _on_connect(self) -> None:
        for handler in self._on_connect_registry:
            await handler(self)

    async def _on_close(self) -> None:
        for handler in self._on_close_registry:
            await handler(self)

    async def start(self) -> None:
        if self._server is not None:
            raise RuntimeError("Controller is already running")

        logger.info(
            f"Starting websocket server on {self.host}:{self.port}",
        )

        self._server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
        )

        try:
            await self._closed.wait()
        finally:
            await self.stop()

    async def stop(self) -> None:
        if self._closed.is_set():
            return

        self._closed.set()
        self._cancel_ping_timeout()

        if self._server is not None:
            logger.info(
                f"Stopping websocket server on {self.host}:{self.port}",
            )

            self._server.close()
            await self._server.wait_closed()
            self._server = None

        if self.websocket is not None:
            await self.websocket.close()
            self.websocket = None

    def send_all(self, message: str) -> None:
        if self.websocket is None:
            return

        asyncio.run_coroutine_threadsafe(
            self.websocket.send(message),
            self.loop,
        )

class SimpleControllerManager:
    def __init__(self, host: str):
        self.host = host
        self.controllers: dict[int, SimpleController] = {}
        self._controller_tasks: dict[int, Future[None]] = {}

        self._loop = asyncio.new_event_loop()

        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
        )
        self._thread.start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def get_controller(self, port: int) -> SimpleController:
        controller = self.controllers.get(port)

        if controller is not None:
            return controller

        controller = SimpleController(
            host=self.host,
            port=port,
            loop=self._loop,
        )

        controller.send_all("Test")

        self.controllers[port] = controller

        future = asyncio.run_coroutine_threadsafe(
            controller.start(),
            self._loop,
        )

        self._controller_tasks[port] = future

        return controller

    def del_controller(self, controller: SimpleController) -> None:
        if self.controllers.get(controller.port) is not controller:
            return

        self.controllers.pop(controller.port)

        future = self._controller_tasks.pop(
            controller.port,
            None,
        )

        asyncio.run_coroutine_threadsafe(
            controller.stop(),
            self._loop,
        )

        if future is not None:
            future.add_done_callback(self._controller_finished)

    @staticmethod
    def _controller_finished(future: Future[None]) -> None:
        try:
            future.result()
        except Exception:
            logger.exception("Controller stopped with an error")

    def stop(self) -> None:
        controllers = list(self.controllers.values())

        for controller in controllers:
            self.del_controller(controller)

        self._loop.call_soon_threadsafe(
            self._loop.stop,
        )

        self._thread.join()
        self._loop.close()


simple_controller_manager = SimpleControllerManager(host="0.0.0.0")
