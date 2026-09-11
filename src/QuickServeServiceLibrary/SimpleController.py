import asyncio
import logging
import threading

from collections.abc import Awaitable, Callable
from concurrent.futures import Future

import websockets

from websockets.asyncio.server import Server, ServerConnection

from QuickServeDriver.instance.base_instance import BaseInstance
from QuickServeDriver.port_manager import port_manager
from QuickServeFS.modules import Service
from QuickServeFS.path_resolver import resolver
from QuickServeFS.modules import Module

MessageHandler = Callable[[str, "SimpleController"], Awaitable[None]]
ConnectionHandler = Callable[["SimpleController"], Awaitable[None]]

PING_TIMEOUT = 120

logger = logging.getLogger(__name__)


class SimpleController:
    def __init__(
        self,
        host: str,
        port: int,
        loop: asyncio.AbstractEventLoop,
        instance: "BaseInstance",
    ):
        self.host = host
        self.port = port
        self.loop = loop

        self.websocket: ServerConnection | None = None

        self.instance: "BaseInstance" = instance
        self.module: "Module" = resolver.modules[instance.module_name]
        self.service: "Service" = self.module.service

        logger.debug(
            f"Initializing controller on {host}:{port} "
            f"for instance {instance}",
        )

        if not hasattr(self.service, "SimpleControllerInit"):
            logger.error(
                f"Service {self.service.NAME} does not support "
                f"SimpleController",
            )
            raise ValueError(
                f"Service {self.service.NAME} doesn't support simple controller"
            )

        self.processor_on_message = self.get_processor_class().on_message

        self._server: Server | None = None
        self._closed = asyncio.Event()
        self._ping_task: asyncio.Task[None] | None = None

        self._on_message_registry: list[MessageHandler] = []
        self._on_connect_registry: list[ConnectionHandler] = []
        self._on_close_registry: list[ConnectionHandler] = []

        logger.debug(
            f"Controller initialized on {self.host}:{self.port}",
        )

    def get_processor_class(self):
        assert hasattr(self.service, "SimpleControllerInit")
        processor = getattr(self.service, "SimpleControllerInit")
        assert hasattr(processor, "on_message")

        return processor

    @property
    def ws_url(self) -> str:
        return f"ws://{self.host}:{self.port}"

    def on_message(self) -> Callable[[MessageHandler], MessageHandler]:
        def decorator(func: MessageHandler) -> MessageHandler:
            logger.debug(
                f"Registered on_message handler {func.__qualname__} "
                f"for controller {self.port}",
            )

            self._on_message_registry.append(func)
            return func

        return decorator

    def on_connect(self) -> Callable[[ConnectionHandler], ConnectionHandler]:
        def decorator(func: ConnectionHandler) -> ConnectionHandler:
            logger.debug(
                f"Registered on_connect handler {func.__qualname__} "
                f"for controller {self.port}",
            )

            self._on_connect_registry.append(func)
            return func

        return decorator

    def on_close(self) -> Callable[[ConnectionHandler], ConnectionHandler]:
        def decorator(func: ConnectionHandler) -> ConnectionHandler:
            logger.debug(
                f"Registered on_close handler {func.__qualname__} "
                f"for controller {self.port}",
            )

            self._on_close_registry.append(func)
            return func

        return decorator

    async def _handle_connection(
        self,
        websocket: ServerConnection,
    ) -> None:
        logger.info(
            f"WebSocket connection established on port {self.port} "
            f"from {websocket.remote_address}",
        )

        if self.websocket is not None:
            logger.warning(
                f"Replacing existing WebSocket connection on port {self.port}. "
                f"Old connection: {self.websocket.remote_address}, "
                f"new connection: {websocket.remote_address}",
            )

        self.websocket = websocket
        self._reset_ping_timeout()

        try:
            logger.debug(
                f"Running on_connect handlers for controller {self.port}",
            )

            await self._on_connect()

            logger.debug(
                f"Listening for messages on controller {self.port}",
            )

            async for message in websocket:
                logger.debug(
                    f"Received message on controller {self.port}: {message!r}",
                )

                await self._on_message(message)

        except websockets.ConnectionClosed as exc:
            logger.info(
                f"WebSocket connection closed on port {self.port}: "
                f"code={exc.code}, reason={exc.reason!r}",
            )

        except Exception:
            logger.exception(
                f"Unhandled exception while handling WebSocket "
                f"connection on port {self.port}",
            )

        finally:
            logger.debug(
                f"Cleaning up WebSocket connection on port {self.port}",
            )

            self._cancel_ping_timeout()

            if self.websocket is websocket:
                self.websocket = None

            await self._on_close()

            port_manager.free(self.port)

            logger.info(
                f"WebSocket connection cleanup complete on port {self.port}",
            )

    async def _on_message(self, message: str) -> None:
        if message.strip() == "simple-ping":
            logger.debug(
                f"Received simple-ping on controller {self.port}",
            )

            self._reset_ping_timeout()
            return

        logger.debug(
            f"Dispatching message to "
            f"{len(self._on_message_registry)} registered handlers "
            f"on controller {self.port}",
        )

        for handler in self._on_message_registry:
            logger.debug(
                f"Calling message handler {handler.__qualname__} "
                f"on controller {self.port}",
            )

            await handler(message, self)

        logger.debug(
            f"Calling service message processor "
            f"for controller {self.port}",
        )

        self.processor_on_message(
            instance=self.instance,
            message=message,
        )

    def _reset_ping_timeout(self) -> None:
        logger.debug(
            f"Resetting ping timeout for controller {self.port}",
        )

        self._cancel_ping_timeout()

        self._ping_task = asyncio.create_task(
            self._ping_timeout(),
        )

    def _cancel_ping_timeout(self) -> None:
        if self._ping_task is not None:
            logger.debug(
                f"Cancelling ping timeout for controller {self.port}",
            )

            self._ping_task.cancel()
            self._ping_task = None

    async def _ping_timeout(self) -> None:
        try:
            await asyncio.sleep(PING_TIMEOUT)

            logger.warning(
                f"Controller on port {self.port} timed out "
                f"after {PING_TIMEOUT} seconds",
            )

            await self.stop()

        except asyncio.CancelledError:
            logger.debug(
                f"Ping timeout cancelled for controller {self.port}",
            )

        except Exception:
            logger.exception(
                f"Error in ping timeout for controller {self.port}",
            )

    async def _on_connect(self) -> None:
        logger.debug(
            f"Executing {len(self._on_connect_registry)} "
            f"on_connect handlers for controller {self.port}",
        )

        for handler in self._on_connect_registry:
            logger.debug(
                f"Calling connect handler {handler.__qualname__} "
                f"on controller {self.port}",
            )

            await handler(self)

    async def _on_close(self) -> None:
        logger.debug(
            f"Executing {len(self._on_close_registry)} "
            f"on_close handlers for controller {self.port}",
        )

        for handler in self._on_close_registry:
            logger.debug(
                f"Calling close handler {handler.__qualname__} "
                f"on controller {self.port}",
            )

            await handler(self)

    async def start(self) -> None:
        if self._server is not None:
            logger.error(
                f"Attempted to start already-running "
                f"controller on port {self.port}",
            )
            raise RuntimeError("Controller is already running")

        logger.info(
            f"Starting WebSocket server on {self.host}:{self.port}",
        )

        try:
            self._server = await websockets.serve(
                self._handle_connection,
                self.host,
                self.port,
            )

            logger.info(
                f"WebSocket server listening on "
                f"{self.host}:{self.port}",
            )

            await self._closed.wait()

        except Exception:
            logger.exception(
                f"Failed while running WebSocket server "
                f"on port {self.port}",
            )
            raise

        finally:
            logger.debug(
                f"Controller start() exiting on port {self.port}",
            )

            await self.stop()

    async def stop(self) -> None:
        if self._closed.is_set():
            logger.debug(
                f"Controller on port {self.port} is already stopped",
            )
            return

        logger.info(
            f"Stopping controller on {self.host}:{self.port}",
        )

        self._closed.set()
        self._cancel_ping_timeout()

        if self._server is not None:
            logger.info(
                f"Stopping WebSocket server on port {self.port}",
            )

            self._server.close()
            await self._server.wait_closed()
            self._server = None

            logger.debug(
                f"WebSocket server stopped on port {self.port}",
            )

        if self.websocket is not None:
            logger.debug(
                f"Closing WebSocket connection on port {self.port}",
            )

            await self.websocket.close()
            self.websocket = None

        logger.info(
            f"Controller on port {self.port} stopped",
        )

    def send_all(self, message: str) -> None:
        if self.websocket is None:
            logger.debug(
                f"Ignoring send on controller {self.port}: "
                f"no active connection",
            )
            return

        logger.debug(
            f"Sending message on controller {self.port}: {message!r}",
        )

        future = asyncio.run_coroutine_threadsafe(
            self.websocket.send(message),
            self.loop,
        )

        def send_finished(future: Future) -> None:
            try:
                future.result()

                logger.debug(
                    f"Message sent successfully "
                    f"on controller {self.port}",
                )

            except Exception:
                logger.exception(
                    f"Failed to send message on controller {self.port}",
                )

        future.add_done_callback(send_finished)


class SimpleControllerManager:
    def __init__(self, host: str):
        self.host = host
        self.controllers: dict[int, SimpleController] = {}
        self._controller_tasks: dict[int, Future[None]] = {}

        logger.info(
            f"Initializing SimpleControllerManager on host {host}",
        )

        self._loop = asyncio.new_event_loop()

        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="SimpleControllerLoop",
        )

        self._thread.start()

        logger.info(
            "SimpleControllerManager initialized; "
            "event loop thread started",
        )

    def _run_loop(self) -> None:
        logger.debug(
            "SimpleController event loop thread starting",
        )

        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_forever()
        finally:
            logger.debug(
                "SimpleController event loop thread exiting",
            )

    def get_controller(
        self,
        port: int,
        instance: "BaseInstance",
    ) -> SimpleController:
        logger.debug(
            f"Getting controller for port {port}",
        )

        controller = self.controllers.get(port)

        if controller is not None:
            logger.debug(
                f"Returning existing controller on port {port}",
            )
            return controller

        logger.info(
            f"Creating new controller on port {port}",
        )

        controller = SimpleController(
            host=self.host,
            port=port,
            loop=self._loop,
            instance=instance,
        )

        self.controllers[port] = controller

        logger.debug(
            f"Registered controller on port {port}",
        )

        future = asyncio.run_coroutine_threadsafe(
            controller.start(),
            self._loop,
        )

        self._controller_tasks[port] = future

        logger.debug(
            f"Started controller task on port {port}",
        )

        return controller

    def del_controller(self, controller: SimpleController) -> None:
        logger.debug(
            f"Deleting controller on port {controller.port}",
        )

        if self.controllers.get(controller.port) is not controller:
            logger.debug(
                f"Controller on port {controller.port} "
                f"is not registered or has already been replaced",
            )
            return

        self.controllers.pop(controller.port)

        future = self._controller_tasks.pop(
            controller.port,
            None,
        )

        logger.info(
            f"Stopping controller on port {controller.port}",
        )

        stop_future = asyncio.run_coroutine_threadsafe(
            controller.stop(),
            self._loop,
        )

        def stop_finished(future: Future[None]) -> None:
            try:
                future.result()

                logger.debug(
                    f"Controller stop completed on port {controller.port}",
                )

            except Exception:
                logger.exception(
                    f"Controller stop failed on port {controller.port}",
                )

        stop_future.add_done_callback(stop_finished)

        if future is not None:
            future.add_done_callback(
                self._controller_finished,
            )

    @staticmethod
    def _controller_finished(future: Future[None]) -> None:
        try:
            future.result()

            logger.debug(
                "Controller task finished successfully",
            )

        except Exception:
            logger.exception(
                "Controller task finished with an error",
            )

    def stop(self) -> None:
        logger.info(
            "Stopping SimpleControllerManager",
        )

        controllers = list(self.controllers.values())

        logger.debug(
            f"Stopping {len(controllers)} controllers",
        )

        for controller in controllers:
            self.del_controller(controller)

        logger.debug(
            "Stopping SimpleController event loop",
        )

        self._loop.call_soon_threadsafe(
            self._loop.stop,
        )

        self._thread.join()

        logger.debug(
            "SimpleController event loop thread joined",
        )

        self._loop.close()

        logger.info(
            "SimpleControllerManager stopped",
        )


simple_controller_manager = SimpleControllerManager(
    host="0.0.0.0",
)
resolver.simple_controller_manager = simple_controller_manager