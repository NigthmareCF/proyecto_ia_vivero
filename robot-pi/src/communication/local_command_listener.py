from __future__ import annotations

import json
import logging
import os
import socket
import threading
from collections.abc import Callable
from pathlib import Path


LOGGER = logging.getLogger(__name__)


class LocalCommandListener:
    def __init__(
        self,
        socket_path: str,
        callback: Callable[[str, dict], None],
        shutdown_event: threading.Event,
    ) -> None:
        self.socket_path = socket_path
        self.callback = callback
        self.shutdown_event = shutdown_event
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        socket_file = Path(self.socket_path)
        socket_file.parent.mkdir(parents=True, exist_ok=True)
        socket_file.unlink(missing_ok=True)
        server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_socket.bind(self.socket_path)
        os.chmod(self.socket_path, 0o666)
        server_socket.listen(4)
        server_socket.settimeout(0.5)
        self._socket = server_socket
        self._thread = threading.Thread(target=self._run, name="local-command-listener", daemon=True)
        self._thread.start()
        LOGGER.info("Local command socket listening at %s", self.socket_path)

    def stop(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        Path(self.socket_path).unlink(missing_ok=True)

    def _run(self) -> None:
        while not self.shutdown_event.is_set():
            try:
                if self._socket is None:
                    return
                connection, _ = self._socket.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            with connection:
                self._handle_connection(connection)

    def _handle_connection(self, connection: socket.socket) -> None:
        try:
            payload = json.loads(connection.recv(4096).decode("utf-8"))
            command = str(payload["command"])
            data = payload.get("data") or {}
            if not isinstance(data, dict):
                raise ValueError("data must be an object")
            self.callback(command, data)
            response = {"ok": True}
        except Exception as exc:
            LOGGER.warning("Local command failed: %s", exc)
            response = {"ok": False, "error": str(exc)}
        try:
            connection.sendall((json.dumps(response) + "\n").encode("utf-8"))
        except OSError:
            LOGGER.debug("Local command client disconnected before receiving the response")
