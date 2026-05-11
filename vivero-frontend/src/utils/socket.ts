export function resolveSockJsUrl(rawUrl?: string) {
  const fallback = "http://localhost:8080/api/ws";
  const value = (rawUrl ?? fallback).trim();

  if (!value) {
    return fallback;
  }

  const normalizedProtocol = value
    .replace(/^ws:\/\//i, "http://")
    .replace(/^wss:\/\//i, "https://");

  return normalizedProtocol.endsWith("/ws")
    ? normalizedProtocol
    : `${normalizedProtocol.replace(/\/+$/, "")}/ws`;
}
