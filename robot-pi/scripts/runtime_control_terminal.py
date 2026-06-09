from __future__ import annotations

import cmd
import json
import socket
import threading
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]
SOCKET_PATH = PROJECT_DIR / "robot-pi-data" / "manual-control.sock"
PULSE_INTERVAL_SECONDS = 0.1


class RuntimeControlShell(cmd.Cmd):
    intro = (
        "\nControl manual seguro del runtime\n"
        "Comandos: adelante, atras, izquierda, derecha, stop, potencia <0-100>, estado, salir\n"
        "Frontend y terminal comparten el mismo runtime. Usa stop antes de dejar la consola.\n"
    )
    prompt = "robot> "

    def __init__(self) -> None:
        super().__init__()
        self.speed = 35
        self.direction = "stop"
        self._shutdown_event = threading.Event()
        self._lock = threading.Lock()
        self._pulse_thread = threading.Thread(target=self._pulse_moves, name="manual-move-pulse", daemon=True)
        self._pulse_thread.start()

    def emptyline(self) -> None:
        return None

    def _send(self, command: str, data: dict | None = None) -> dict:
        payload = json.dumps({"command": command, "data": data or {}}).encode("utf-8")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(1.0)
            client.connect(str(SOCKET_PATH))
            client.sendall(payload)
            return json.loads(client.recv(4096).decode("utf-8"))

    def _send_move(self) -> None:
        with self._lock:
            direction = self.direction
            speed = self.speed if direction != "stop" else 0
        self._send("MOVE", {"direction": direction, "speed": speed})

    def _pulse_moves(self) -> None:
        while not self._shutdown_event.wait(PULSE_INTERVAL_SECONDS):
            with self._lock:
                active = self.direction != "stop"
            if active:
                try:
                    self._send_move()
                except OSError:
                    pass

    def _move(self, direction: str) -> None:
        with self._lock:
            self.direction = direction
        try:
            self._send_move()
            print(f"OK: {direction} activo a {self.speed}%")
        except OSError as exc:
            print(f"ERROR: runtime no disponible en {SOCKET_PATH}: {exc}")

    def do_adelante(self, _arg: str) -> None:
        self._move("forward")

    def do_atras(self, _arg: str) -> None:
        self._move("backward")

    def do_izquierda(self, _arg: str) -> None:
        self._move("left")

    def do_derecha(self, _arg: str) -> None:
        self._move("right")

    def do_stop(self, _arg: str) -> None:
        with self._lock:
            self.direction = "stop"
        try:
            self._send_move()
            print("OK: motores detenidos")
        except OSError as exc:
            print(f"ERROR: runtime no disponible en {SOCKET_PATH}: {exc}")

    def do_potencia(self, arg: str) -> None:
        try:
            speed = int(arg.strip())
        except ValueError:
            print("Uso: potencia <0-100>")
            return
        with self._lock:
            self.speed = max(0, min(speed, 100))
        try:
            self._send_move()
            print(f"OK: potencia {self.speed}%")
        except OSError as exc:
            print(f"ERROR: runtime no disponible en {SOCKET_PATH}: {exc}")

    def do_estado(self, _arg: str) -> None:
        print(f"direccion={self.direction} potencia={self.speed}% socket={SOCKET_PATH}")

    def do_salir(self, _arg: str) -> bool:
        self.close()
        print("Motores detenidos. Cerrando.")
        return True

    def do_exit(self, arg: str) -> bool:
        return self.do_salir(arg)

    def do_quit(self, arg: str) -> bool:
        return self.do_salir(arg)

    def do_EOF(self, arg: str) -> bool:
        print()
        return self.do_salir(arg)

    def close(self) -> None:
        self._shutdown_event.set()
        with self._lock:
            self.direction = "stop"
        try:
            self._send_move()
        except OSError:
            pass


def main() -> int:
    shell = RuntimeControlShell()
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nInterrumpido.")
        shell.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
