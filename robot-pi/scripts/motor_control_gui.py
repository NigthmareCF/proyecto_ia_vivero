from __future__ import annotations

import logging
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src.navigation import motor_controller  # noqa: E402


LOGGER = logging.getLogger("motor_control_gui")


class MotorControlApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Control motores robot")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.vars = {
            "IN1": tk.IntVar(value=0),
            "IN2": tk.IntVar(value=0),
            "IN3": tk.IntVar(value=0),
            "IN4": tk.IntVar(value=0),
            "ENA": tk.IntVar(value=0),
            "ENB": tk.IntVar(value=0),
        }
        self.status = tk.StringVar(value="Listo. Todo en 0.")
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(250, self._raise_window)

    def _raise_window(self) -> None:
        self.lift()
        self.focus_force()
        self.attributes("-topmost", False)

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="IN 1-4").grid(row=0, column=0, columnspan=4, sticky="w")
        for col, name in enumerate(["IN1", "IN2", "IN3", "IN4"]):
            ttk.Label(frame, text=name).grid(row=1, column=col, padx=6, pady=(8, 2))
            ttk.Spinbox(frame, from_=0, to=1, width=5, textvariable=self.vars[name]).grid(row=2, column=col, padx=6)

        ttk.Label(frame, text="ENA / ENB").grid(row=3, column=0, columnspan=4, sticky="w", pady=(16, 0))
        for col, name in enumerate(["ENA", "ENB"]):
            ttk.Label(frame, text=name).grid(row=4, column=col, padx=6, pady=(8, 2))
            ttk.Spinbox(frame, from_=0, to=100, width=7, textvariable=self.vars[name]).grid(row=5, column=col, padx=6)

        ttk.Button(frame, text="Aplicar", command=self.apply).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(16, 0), padx=6)
        ttk.Button(frame, text="STOP", command=self.stop).grid(row=6, column=2, columnspan=2, sticky="ew", pady=(16, 0), padx=6)
        ttk.Label(frame, textvariable=self.status).grid(row=7, column=0, columnspan=4, sticky="w", pady=(12, 0))

    def _value(self, name: str, low: int, high: int) -> int:
        value = int(self.vars[name].get())
        value = max(low, min(value, high))
        self.vars[name].set(value)
        return value

    def apply(self) -> None:
        try:
            in1 = self._value("IN1", 0, 1)
            in2 = self._value("IN2", 0, 1)
            in3 = self._value("IN3", 0, 1)
            in4 = self._value("IN4", 0, 1)
            ena = self._value("ENA", 0, 100)
            enb = self._value("ENB", 0, 100)
        except (tk.TclError, ValueError):
            messagebox.showerror("Valor invalido", "IN1-IN4 usan 0/1. ENA/ENB usan 0-100.")
            return
        motor_controller.apply_raw(in1, in2, in3, in4, ena, enb)
        self.status.set(f"Aplicado: IN1={in1} IN2={in2} IN3={in3} IN4={in4} ENA={ena}% ENB={enb}%")

    def stop(self) -> None:
        motor_controller.stop()
        for name in self.vars:
            self.vars[name].set(0)
        self.status.set("STOP aplicado. Todo en 0.")

    def close(self) -> None:
        motor_controller.cleanup()
        self.destroy()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    motor_controller.setup()
    app = MotorControlApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
