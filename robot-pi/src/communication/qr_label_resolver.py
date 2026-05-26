from __future__ import annotations

import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests


LABEL_PATTERN = re.compile(r"\bPLA_\d+_MA_\d+_(?:IZ|DR)\b", re.IGNORECASE)


class QrLabelResolver:
    def __init__(self, cache_path: str, request_timeout_seconds: float = 1.8) -> None:
        self._cache_path = Path(cache_path)
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._request_timeout_seconds = request_timeout_seconds
        self._lock = threading.Lock()
        self._initialize()

    def resolve(self, raw_payload: str | None) -> dict[str, Any]:
        started_at = time.time()
        normalized_raw_payload = str(raw_payload or "").strip()
        if not normalized_raw_payload:
            return self._build_result(
                raw_payload="",
                resolved_label=None,
                resolution_source="empty",
                started_at=started_at,
                cache_hit=False,
                page_text=None,
                error="EMPTY_QR_PAYLOAD",
            )

        direct_label = self._extract_label(normalized_raw_payload)
        if direct_label:
            self._upsert_mapping(normalized_raw_payload, direct_label, "direct", None)
            return self._build_result(
                raw_payload=normalized_raw_payload,
                resolved_label=direct_label,
                resolution_source="direct",
                started_at=started_at,
                cache_hit=False,
                page_text=None,
                error=None,
            )

        cached_label = self._lookup_mapping(normalized_raw_payload)
        if cached_label:
            return self._build_result(
                raw_payload=normalized_raw_payload,
                resolved_label=cached_label,
                resolution_source="cache",
                started_at=started_at,
                cache_hit=True,
                page_text=None,
                error=None,
            )

        if not self._is_url(normalized_raw_payload):
            return self._build_result(
                raw_payload=normalized_raw_payload,
                resolved_label=normalized_raw_payload.upper(),
                resolution_source="passthrough",
                started_at=started_at,
                cache_hit=False,
                page_text=None,
                error=None,
            )

        try:
            response = requests.get(
                normalized_raw_payload,
                headers={"User-Agent": "AgroBot-QR-Resolver/1.0"},
                timeout=self._request_timeout_seconds,
                allow_redirects=True,
            )
            response.raise_for_status()
            page_text = " ".join(response.text.split())
        except requests.RequestException as exc:
            return self._build_result(
                raw_payload=normalized_raw_payload,
                resolved_label=normalized_raw_payload.upper(),
                resolution_source="url_error",
                started_at=started_at,
                cache_hit=False,
                page_text=None,
                error=str(exc),
            )

        extracted_label = self._extract_label(response.url) or self._extract_label(page_text)
        if extracted_label:
            self._upsert_mapping(normalized_raw_payload, extracted_label, "url_text", response.url)
        return self._build_result(
            raw_payload=normalized_raw_payload,
            resolved_label=extracted_label or normalized_raw_payload.upper(),
            resolution_source="url_text" if extracted_label else "url_passthrough",
            started_at=started_at,
            cache_hit=False,
            page_text=page_text[:1200] if page_text else None,
            error=None,
            resolved_url=response.url,
        )

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS qr_label_cache (
                    raw_payload TEXT PRIMARY KEY,
                    resolved_label TEXT NOT NULL,
                    resolution_source TEXT NOT NULL,
                    resolved_url TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._cache_path)

    def _lookup_mapping(self, raw_payload: str) -> str | None:
        with self._lock:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT resolved_label FROM qr_label_cache WHERE raw_payload = ?",
                    (raw_payload,),
                ).fetchone()
        return str(row[0]).upper() if row and row[0] else None

    def _upsert_mapping(
        self,
        raw_payload: str,
        resolved_label: str,
        resolution_source: str,
        resolved_url: str | None,
    ) -> None:
        now = time.time()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO qr_label_cache (
                        raw_payload,
                        resolved_label,
                        resolution_source,
                        resolved_url,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(raw_payload) DO UPDATE SET
                        resolved_label = excluded.resolved_label,
                        resolution_source = excluded.resolution_source,
                        resolved_url = excluded.resolved_url,
                        updated_at = excluded.updated_at
                    """,
                    (raw_payload, resolved_label, resolution_source, resolved_url, now, now),
                )
                connection.commit()

    def _extract_label(self, text: str | None) -> str | None:
        if not text:
            return None
        match = LABEL_PATTERN.search(text)
        return match.group(0).upper() if match else None

    def _is_url(self, value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def _build_result(
        self,
        raw_payload: str,
        resolved_label: str | None,
        resolution_source: str,
        started_at: float,
        cache_hit: bool,
        page_text: str | None,
        error: str | None,
        resolved_url: str | None = None,
    ) -> dict[str, Any]:
        completed_at = time.time()
        return {
            "rawPayload": raw_payload,
            "resolvedLabel": str(resolved_label).upper() if resolved_label else None,
            "resolutionSource": resolution_source,
            "cacheHit": cache_hit,
            "resolvedUrl": resolved_url,
            "pageTextPreview": page_text,
            "error": error,
            "startedAt": started_at,
            "completedAt": completed_at,
            "latencyMs": round((completed_at - started_at) * 1000, 1),
        }
