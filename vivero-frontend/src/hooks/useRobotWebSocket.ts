import { Client } from "@stomp/stompjs";
import SockJS from "sockjs-client";
import { useEffect } from "react";
import { useRobotStore } from "../store/robotStore";

export function useRobotWebSocket() {
  const setStatus = useRobotStore((state) => state.setStatus);

  useEffect(() => {
    const client = new Client({
      webSocketFactory: () => new SockJS((import.meta.env.VITE_WS_URL ?? "http://localhost:8080/api") + "/ws"),
      reconnectDelay: 5000,
      onConnect: () => {
        client.subscribe("/topic/robot/status", (message) => setStatus(JSON.parse(message.body)));
      },
    });

    client.activate();
    return () => {
      void client.deactivate();
    };
  }, [setStatus]);
}
