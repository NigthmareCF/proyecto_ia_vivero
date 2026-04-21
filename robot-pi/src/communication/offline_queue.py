from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path


class OfflineObservationQueue:
    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def enqueue(self, payload: dict) -> str:
        entry_id = f"{int(time.time() * 1000)}-{uuid.uuid4().hex}"
        path = self._entry_path(entry_id)
        with self._lock:
            path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
        return entry_id

    def peek_oldest(self) -> tuple[str, dict] | None:
        with self._lock:
            entries = sorted(self._base_dir.glob("*.json"))
            if not entries:
                return None
            path = entries[0]
            payload = json.loads(path.read_text(encoding="utf-8"))
            return path.stem, payload

    def remove(self, entry_id: str) -> None:
        path = self._entry_path(entry_id)
        with self._lock:
            if path.exists():
                path.unlink()

    def size(self) -> int:
        with self._lock:
            return sum(1 for _ in self._base_dir.glob("*.json"))

    def _entry_path(self, entry_id: str) -> Path:
        return self._base_dir / f"{entry_id}.json"
