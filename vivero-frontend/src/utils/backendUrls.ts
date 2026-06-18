const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "0.0.0.0"]);
const PUBLIC_FRONT_DOOR_HOSTS = new Set([
  "agrotechnologyrobotics.com",
  "www.agrotechnologyrobotics.com",
  "agrotechnologyrobtics.com",
  "www.agrotechnologyrobtics.com",
]);

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, "");
}

function canUseBrowserLocation() {
  return typeof window !== "undefined" && typeof window.location !== "undefined";
}

function shouldUseSameOriginProxy(configuredUrl?: string) {
  if (!canUseBrowserLocation()) {
    return false;
  }
  const browserHost = window.location.hostname;
  if (!browserHost || LOOPBACK_HOSTS.has(browserHost)) {
    return false;
  }
  if (PUBLIC_FRONT_DOOR_HOSTS.has(browserHost)) {
    return true;
  }
  if (!configuredUrl) {
    return true;
  }
  try {
    const parsed = new URL(configuredUrl, window.location.origin);
    return LOOPBACK_HOSTS.has(parsed.hostname);
  } catch {
    return true;
  }
}

export function resolveApiBaseUrl() {
  const configuredUrl = import.meta.env.VITE_API_URL?.trim();
  if (shouldUseSameOriginProxy(configuredUrl)) {
    return "/api";
  }
  return trimTrailingSlash(configuredUrl || "http://localhost:8080/api");
}

export function resolveBackendWsBaseUrl() {
  const configuredWsUrl = import.meta.env.VITE_WS_URL?.trim();
  const configuredApiUrl = import.meta.env.VITE_API_URL?.trim();
  if (shouldUseSameOriginProxy(configuredWsUrl || configuredApiUrl)) {
    const protocol = canUseBrowserLocation() && window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/api/ws`;
  }
  if (configuredWsUrl) {
    return trimTrailingSlash(configuredWsUrl);
  }
  const apiBaseUrl = resolveApiBaseUrl();
  if (apiBaseUrl.startsWith("/")) {
    const protocol = canUseBrowserLocation() && window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}${apiBaseUrl}/ws`;
  }
  return `${apiBaseUrl.replace(/^http/i, "ws")}/ws`;
}

export function resolveBackendAssetUrl(assetPath: string) {
  if (assetPath.startsWith("http://") || assetPath.startsWith("https://")) {
    return assetPath;
  }
  if (assetPath.startsWith("/api/")) {
    return assetPath;
  }
  const apiBaseUrl = resolveApiBaseUrl();
  if (apiBaseUrl.startsWith("/")) {
    return assetPath.startsWith("/") ? assetPath : `${apiBaseUrl}/${assetPath}`;
  }
  const normalizedApiBaseUrl = trimTrailingSlash(apiBaseUrl);
  const serverBaseUrl = normalizedApiBaseUrl.replace(/\/api$/, "");
  return assetPath.startsWith("/")
    ? `${serverBaseUrl}${assetPath}`
    : `${normalizedApiBaseUrl}/${assetPath}`;
}
