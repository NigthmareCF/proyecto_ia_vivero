from __future__ import annotations

import cmd
import logging
import shlex
import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src.navigation import motor_controller  # noqa: E402


LOGGER = logging.getLogger("motor_control_terminal")


class MotorControlShell(cmd.Cmd):
    intro = (
        "\nControl manual de motores\n"
        "Comandos: adelante, atras, izquierda, derecha, stop, iniciar, potencia <0-100>, estado, ayuda, salir\n"
        "Calibracion por lado: iz adelante, iz atras, iz stop, dr adelante, dr atras, dr stop\n"
        "Diagnostico L298N: pines, canal ena adelante, canal enb atras, raw <IN1> <IN2> <IN3> <IN4> <ENA> <ENB>\n"
        "Control directo: in1 0|1, in2 0|1, in3 0|1, in4 0|1, ena 0-100, enb 0-100\n"
        "Pin individual: pin IN1, pin IN2, pin IN3, pin IN4\n"
        "La ultima accion queda activa hasta cambiarla o ejecutar stop.\n"
    )
    prompt = "motores> "

    def __init__(self, default_speed: int) -> None:
        super().__init__()
        self.speed = max(0, min(default_speed, 100))
        self.current_action: str | None = None
        self.last_action: str | None = None
        self.raw_state = {
            "IN1": 0,
            "IN2": 0,
            "IN3": 0,
            "IN4": 0,
            "ENA": 0,
            "ENB": 0,
        }
        self.actions = {
            "adelante": motor_controller.move_forward,
            "atras": motor_controller.move_backward,
            "izquierda": motor_controller.turn_left,
            "derecha": motor_controller.turn_right,
        }

    def emptyline(self) -> None:
        return None

    def do_ayuda(self, arg: str) -> None:
        print("adelante              Mantiene avance hacia adelante")
        print("atras                 Mantiene reversa")
        print("izquierda | iz        Mantiene giro a la izquierda")
        print("derecha | dr          Mantiene giro a la derecha")
        print("iz adelante|atras     Prueba solo motores izquierdos")
        print("dr adelante|atras     Prueba solo motores derechos")
        print("iz stop | dr stop      Detiene ambos motores")
        print("pines                 Muestra GPIO asignados a IN1/IN2/IN3/IN4/ENA/ENB")
        print("canal ena adelante    IN1=1 IN2=0 ENA=potencia, ENB=0")
        print("canal ena atras       IN1=0 IN2=1 ENA=potencia, ENB=0")
        print("canal enb adelante    IN3=1 IN4=0 ENB=potencia, ENA=0")
        print("canal enb atras       IN3=0 IN4=1 ENB=potencia, ENA=0")
        print("raw a b c d e f       Envia IN1=a IN2=b IN3=c IN4=d ENA=e ENB=f")
        print("in1|in2|in3|in4 0|1   Cambia un IN y aplica el estado directo")
        print("ena|enb 0-100         Cambia PWM de ENA/ENB y aplica el estado directo")
        print("pin IN1|IN2|IN3|IN4   Activa un solo IN con ENA/ENB a potencia")
        print("potencia <0-100>      Cambia potencia PWM y reaplica la accion actual")
        print("iniciar               Reanuda la ultima accion usada")
        print("stop                  Detiene motores")
        print("estado                Muestra accion y potencia")
        print("salir                 Detiene motores y cierra")

    def do_help(self, arg: str) -> None:
        self.do_ayuda(arg)

    def _run_action(self, name: str) -> None:
        action = self.actions[name]
        action(self.speed)
        self.current_action = name
        self.last_action = name
        print(f"OK: {name} activo a {self.speed}%")

    def do_adelante(self, arg: str) -> None:
        self._run_action("adelante")

    def do_atras(self, arg: str) -> None:
        self._run_action("atras")

    def do_izquierda(self, arg: str) -> None:
        self._run_action("izquierda")

    def do_iz(self, arg: str) -> None:
        self._run_side("iz", arg)

    def do_derecha(self, arg: str) -> None:
        self._run_action("derecha")

    def do_dr(self, arg: str) -> None:
        self._run_side("dr", arg)

    def do_pines(self, arg: str) -> None:
        for name, pin in motor_controller.pin_map().items():
            print(f"{name}=GPIO{pin}")

    def do_canal(self, arg: str) -> None:
        parts = shlex.split(arg.lower())
        if len(parts) != 2 or parts[0] not in {"ena", "enb"} or parts[1] not in {"adelante", "atras"}:
            print("Uso: canal ena|enb adelante|atras")
            return
        channel, direction = parts
        if channel == "ena" and direction == "adelante":
            motor_controller.apply_raw(1, 0, 0, 0, self.speed, 0)
        elif channel == "ena" and direction == "atras":
            motor_controller.apply_raw(0, 1, 0, 0, self.speed, 0)
        elif channel == "enb" and direction == "adelante":
            motor_controller.apply_raw(0, 0, 1, 0, 0, self.speed)
        elif channel == "enb" and direction == "atras":
            motor_controller.apply_raw(0, 0, 0, 1, 0, self.speed)
        self.current_action = f"canal {channel} {direction}"
        self.last_action = self.current_action
        print(f"OK: {self.current_action} a {self.speed}%")

    def _set_raw_state(self, in1: int, in2: int, in3: int, in4: int, ena: int, enb: int) -> None:
        self.raw_state.update({"IN1": in1, "IN2": in2, "IN3": in3, "IN4": in4, "ENA": ena, "ENB": enb})

    def _apply_raw_state(self) -> None:
        motor_controller.apply_raw(
            self.raw_state["IN1"],
            self.raw_state["IN2"],
            self.raw_state["IN3"],
            self.raw_state["IN4"],
            self.raw_state["ENA"],
            self.raw_state["ENB"],
        )
        self.current_action = "directo"
        self.last_action = self.current_action

    def _print_raw_state(self) -> None:
        print(
            "OK: "
            f"IN1={self.raw_state['IN1']} "
            f"IN2={self.raw_state['IN2']} "
            f"IN3={self.raw_state['IN3']} "
            f"IN4={self.raw_state['IN4']} "
            f"ENA={self.raw_state['ENA']}% "
            f"ENB={self.raw_state['ENB']}%"
        )

    def _set_input(self, name: str, arg: str) -> None:
        parts = shlex.split(arg)
        if len(parts) != 1:
            print(f"Uso: {name.lower()} 0|1")
            return
        try:
            value = int(parts[0])
        except ValueError:
            print(f"Valor invalido. Usa: {name.lower()} 0|1")
            return
        if value not in {0, 1}:
            print(f"Valor invalido. Usa: {name.lower()} 0|1")
            return
        self.raw_state[name] = value
        self._apply_raw_state()
        self._print_raw_state()

    def _set_enable(self, name: str, arg: str) -> None:
        parts = shlex.split(arg)
        if len(parts) != 1:
            print(f"Uso: {name.lower()} 0-100")
            return
        try:
            value = int(parts[0])
        except ValueError:
            print(f"Valor invalido. Usa: {name.lower()} 0-100")
            return
        self.raw_state[name] = max(0, min(value, 100))
        self._apply_raw_state()
        self._print_raw_state()

    def do_in1(self, arg: str) -> None:
        self._set_input("IN1", arg)

    def do_in2(self, arg: str) -> None:
        self._set_input("IN2", arg)

    def do_in3(self, arg: str) -> None:
        self._set_input("IN3", arg)

    def do_in4(self, arg: str) -> None:
        self._set_input("IN4", arg)

    def do_ena(self, arg: str) -> None:
        self._set_enable("ENA", arg)

    def do_enb(self, arg: str) -> None:
        self._set_enable("ENB", arg)

    def do_raw(self, arg: str) -> None:
        parts = shlex.split(arg)
        if len(parts) != 6:
            print("Uso: raw <IN1 0/1> <IN2 0/1> <IN3 0/1> <IN4 0/1> <ENA 0-100> <ENB 0-100>")
            return
        try:
            in1, in2, in3, in4 = [1 if int(value) else 0 for value in parts[:4]]
            ena, enb = [max(0, min(int(value), 100)) for value in parts[4:]]
        except ValueError:
            print("Valores invalidos. IN1-IN4 usan 0/1; ENA/ENB usan 0-100.")
            return
        self._set_raw_state(in1, in2, in3, in4, ena, enb)
        motor_controller.apply_raw(in1, in2, in3, in4, ena, enb)
        self.current_action = f"raw {in1} {in2} {in3} {in4} {ena} {enb}"
        self.last_action = self.current_action
        print(f"OK: IN1={in1} IN2={in2} IN3={in3} IN4={in4} ENA={ena}% ENB={enb}%")

    def do_pin(self, arg: str) -> None:
        pin = arg.strip().upper()
        patterns = {
            "IN1": (1, 0, 0, 0),
            "IN2": (0, 1, 0, 0),
            "IN3": (0, 0, 1, 0),
            "IN4": (0, 0, 0, 1),
        }
        if pin not in patterns:
            print("Uso: pin IN1 | pin IN2 | pin IN3 | pin IN4")
            return
        in1, in2, in3, in4 = patterns[pin]
        motor_controller.apply_raw(in1, in2, in3, in4, self.speed, self.speed)
        self.current_action = f"pin {pin}"
        self.last_action = self.current_action
        print(f"OK: {pin}=1, demas IN=0, ENA={self.speed}% ENB={self.speed}%")

    def _run_side(self, side: str, arg: str) -> None:
        parts = shlex.split(arg)
        if not parts:
            if side == "iz":
                self.do_izquierda(arg)
            else:
                self.do_derecha(arg)
            return
        command = parts[0].lower()
        side_label = "izquierdos" if side == "iz" else "derechos"
        if command == "adelante":
            action = motor_controller.move_left_forward if side == "iz" else motor_controller.move_right_forward
            action(self.speed)
            self.current_action = f"{side} adelante"
            self.last_action = self.current_action
            print(f"OK: motores {side_label} adelante a {self.speed}%")
            return
        if command == "atras":
            action = motor_controller.move_left_backward if side == "iz" else motor_controller.move_right_backward
            action(self.speed)
            self.current_action = f"{side} atras"
            self.last_action = self.current_action
            print(f"OK: motores {side_label} atras a {self.speed}%")
            return
        if command == "stop":
            self.do_stop(arg)
            return
        print(f"Uso: {side} adelante | {side} atras | {side} stop")

    def do_potencia(self, arg: str) -> None:
        parts = shlex.split(arg)
        if len(parts) != 1:
            print("Uso: potencia <0-100>")
            return
        try:
            speed = int(parts[0])
        except ValueError:
            print("Potencia invalida. Usa un entero de 0 a 100.")
            return
        self.speed = max(0, min(speed, 100))
        if self.current_action == "iz adelante":
            motor_controller.move_left_forward(self.speed)
            print(f"OK: potencia {self.speed}% aplicada a motores izquierdos adelante")
        elif self.current_action == "iz atras":
            motor_controller.move_left_backward(self.speed)
            print(f"OK: potencia {self.speed}% aplicada a motores izquierdos atras")
        elif self.current_action == "dr adelante":
            motor_controller.move_right_forward(self.speed)
            print(f"OK: potencia {self.speed}% aplicada a motores derechos adelante")
        elif self.current_action == "dr atras":
            motor_controller.move_right_backward(self.speed)
            print(f"OK: potencia {self.speed}% aplicada a motores derechos atras")
        elif self.current_action:
            if self.current_action in self.actions:
                self.actions[self.current_action](self.speed)
                print(f"OK: potencia {self.speed}% aplicada a {self.current_action}")
            else:
                print("OK: potencia configurada. Para control directo usa ena <0-100> o enb <0-100>.")
        else:
            print(f"OK: potencia {self.speed}% configurada")

    def do_iniciar(self, arg: str) -> None:
        if not self.last_action:
            print("No hay accion previa. Usa adelante, atras, izquierda o derecha.")
            return
        if self.last_action == "iz adelante":
            motor_controller.move_left_forward(self.speed)
            self.current_action = self.last_action
            print(f"OK: motores izquierdos adelante a {self.speed}%")
            return
        if self.last_action == "iz atras":
            motor_controller.move_left_backward(self.speed)
            self.current_action = self.last_action
            print(f"OK: motores izquierdos atras a {self.speed}%")
            return
        if self.last_action == "dr adelante":
            motor_controller.move_right_forward(self.speed)
            self.current_action = self.last_action
            print(f"OK: motores derechos adelante a {self.speed}%")
            return
        if self.last_action == "dr atras":
            motor_controller.move_right_backward(self.speed)
            self.current_action = self.last_action
            print(f"OK: motores derechos atras a {self.speed}%")
            return
        if self.last_action.startswith("canal ") or self.last_action.startswith("raw "):
            print("Repite el comando de diagnostico manualmente para evitar enviar una senal cruda accidental.")
            return
        self._run_action(self.last_action)

    def do_stop(self, arg: str) -> None:
        motor_controller.stop()
        self._set_raw_state(0, 0, 0, 0, 0, 0)
        self.current_action = None
        print("OK: motores detenidos")

    def do_estado(self, arg: str) -> None:
        action = self.current_action or "detenido"
        last = self.last_action or "ninguna"
        print(
            f"accion={action} ultima={last} potencia={self.speed}% "
            f"IN1={self.raw_state['IN1']} IN2={self.raw_state['IN2']} "
            f"IN3={self.raw_state['IN3']} IN4={self.raw_state['IN4']} "
            f"ENA={self.raw_state['ENA']}% ENB={self.raw_state['ENB']}%"
        )

    def do_salir(self, arg: str) -> bool:
        motor_controller.stop()
        print("Motores detenidos. Cerrando.")
        return True

    def do_exit(self, arg: str) -> bool:
        return self.do_salir(arg)

    def do_quit(self, arg: str) -> bool:
        return self.do_salir(arg)

    def do_EOF(self, arg: str) -> bool:
        print()
        return self.do_salir(arg)

    def default(self, line: str) -> None:
        print(f"Comando no reconocido: {line}. Escribe ayuda.")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    motor_controller.setup()
    shell = MotorControlShell(default_speed=35)
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nInterrumpido.")
    finally:
        LOGGER.info("Deteniendo motores y limpiando GPIO")
        motor_controller.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
