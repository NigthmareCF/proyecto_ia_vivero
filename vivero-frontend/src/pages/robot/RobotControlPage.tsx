import { useRobotWebSocket } from "../../hooks/useRobotWebSocket";
import { useRobotStore } from "../../store/robotStore";
import { sendRobotCommand } from "../../api/robotApi";

export function RobotControlPage() {
  const robot = useRobotStore();
  useRobotWebSocket();

  return (
    <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h2 className="font-display text-3xl">Control del robot</h2>
        <p className="mt-2 text-sm text-moss">Modo {robot.mode} · bateria {robot.batteryLevel}%</p>
        <div className="mt-6 grid grid-cols-3 gap-3">
          {["FORWARD", "LEFT", "RIGHT", "STOP"].map((command) => (
            <button
              key={command}
              className="rounded-2xl bg-ink px-4 py-3 text-white"
              onClick={() => sendRobotCommand(command)}
            >
              {command}
            </button>
          ))}
        </div>
      </article>
      <article className="rounded-[2rem] bg-ink p-6 text-sand shadow-sm">
        <h2 className="font-display text-3xl">Camara y estado</h2>
        <div className="mt-4 grid min-h-80 place-items-center rounded-[1.5rem] border border-white/20 bg-white/5">
          Stream WebSocket del robot
        </div>
      </article>
    </section>
  );
}
