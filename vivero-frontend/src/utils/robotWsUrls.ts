import { resolveBackendWsBaseUrl } from "./backendUrls";

export function resolveRobotSockJsUrl() {
  return resolveBackendWsBaseUrl().replace(/^ws/i, "http");
}

export function resolveRobotStreamWsUrl() {
  const wsBaseUrl = resolveBackendWsBaseUrl();
  const baseUrl = wsBaseUrl.endsWith("/robot-stream") ? wsBaseUrl : `${wsBaseUrl}/robot-stream`;

  return baseUrl.includes("?") ? `${baseUrl}&role=viewer` : `${baseUrl}?role=viewer`;
}
