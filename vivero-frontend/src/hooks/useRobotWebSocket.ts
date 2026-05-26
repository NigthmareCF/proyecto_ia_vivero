import { Client } from "@stomp/stompjs";
import SockJS from "sockjs-client";
import { useEffect } from "react";
import { getRobotStatus } from "../api/robotApi";
import { normalizeRobotStatus, useRobotStore } from "../store/robotStore";
import { resolveRobotSockJsUrl } from "../utils/robotWsUrls";

export function useRobotWebSocket() {
  const setStatus = useRobotStore((state) => state.setStatus);

  useEffect(() => {
    void getRobotStatus()
      .then((status) => setStatus({ ...normalizeRobotStatus(status), isConnected: true }))
      .catch(() => setStatus({ isConnected: false, connectionQuality: "OFFLINE" }));

    const client = new Client({
      webSocketFactory: () => new SockJS(resolveRobotSockJsUrl()),
      reconnectDelay: 5000,
      onConnect: () => {
        setStatus({ isConnected: true, connectionQuality: "GOOD" });
        client.subscribe("/topic/robot/status", (message) =>
          setStatus({ ...normalizeRobotStatus(JSON.parse(message.body)), isConnected: true }),
        );
      },
      onDisconnect: () => setStatus({ isConnected: false, connectionQuality: "OFFLINE" }),
      onWebSocketClose: () => setStatus({ isConnected: false, connectionQuality: "OFFLINE" }),
      onStompError: () => setStatus({ isConnected: false, connectionQuality: "OFFLINE" }),
    });

    client.activate();
    return () => {
      void client.deactivate();
    };
  }, [setStatus]);
}
