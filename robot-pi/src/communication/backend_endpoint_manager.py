from __future__ import annotations

import threading
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


def _normalize_base_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    path = parsed.path.rstrip("/") or "/api"
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def _base_to_ws_url(base_url: str) -> str:
    parsed = urlsplit(base_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    path = parsed.path.rstrip("/") or "/api"
    return urlunsplit((scheme, parsed.netloc, path, "", ""))


@dataclass(frozen=True)
class BackendEndpointSnapshot:
    base_url: str
    ws_url: str


class BackendEndpointManager:
    def __init__(self, base_urls: list[str]) -> None:
        normalized = [_normalize_base_url(url) for url in base_urls if str(url).strip()]
        self._base_urls = normalized or ["http://localhost:3000/api"]
        self._index = 0
        self._lock = threading.Lock()

    @property
    def candidate_count(self) -> int:
        return len(self._base_urls)

    def current(self) -> BackendEndpointSnapshot:
        with self._lock:
            base_url = self._base_urls[self._index]
            return BackendEndpointSnapshot(base_url=base_url, ws_url=_base_to_ws_url(base_url))

    def mark_success(self, base_url: str | None = None) -> None:
        if base_url is None:
            return
        normalized = _normalize_base_url(base_url)
        with self._lock:
            for index, candidate in enumerate(self._base_urls):
                if candidate == normalized:
                    self._index = index
                    return

    def mark_failure(self, base_url: str | None = None) -> BackendEndpointSnapshot:
        with self._lock:
            if base_url is not None:
                normalized = _normalize_base_url(base_url)
                for index, candidate in enumerate(self._base_urls):
                    if candidate == normalized:
                        self._index = (index + 1) % len(self._base_urls)
                        break
                else:
                    self._index = (self._index + 1) % len(self._base_urls)
            else:
                self._index = (self._index + 1) % len(self._base_urls)
            base_url = self._base_urls[self._index]
            return BackendEndpointSnapshot(base_url=base_url, ws_url=_base_to_ws_url(base_url))

