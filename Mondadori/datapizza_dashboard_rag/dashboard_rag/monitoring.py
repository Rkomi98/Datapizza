from __future__ import annotations

import json
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterator, Optional

import pandas as pd
from opentelemetry import trace


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MonitoringStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_event(
        self,
        event_type: str,
        status: str,
        dataset_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> None:
        payload = {
            "timestamp": _utc_now(),
            "event_type": event_type,
            "status": status,
            "dataset_id": dataset_id,
            "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
            "metadata": metadata or {},
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def load_events(self) -> pd.DataFrame:
        if not self.path.exists():
            return pd.DataFrame(
                columns=["timestamp", "event_type", "status", "dataset_id", "duration_ms", "metadata"]
            )

        rows = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        frame = pd.DataFrame(rows)
        if frame.empty:
            return pd.DataFrame(
                columns=["timestamp", "event_type", "status", "dataset_id", "duration_ms", "metadata"]
            )

        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
        return frame.sort_values("timestamp", ascending=False).reset_index(drop=True)


@contextmanager
def monitored_operation(
    store: MonitoringStore,
    event_type: str,
    dataset_id: Optional[str] = None,
    metadata: Optional[Dict[str, object]] = None,
) -> Iterator[None]:
    start = time.perf_counter()
    tracer = trace.get_tracer("datapizza_dashboard_rag")

    with tracer.start_as_current_span(event_type) as span:
        if dataset_id:
            span.set_attribute("app.dataset_id", dataset_id)
        for key, value in (metadata or {}).items():
            span.set_attribute(f"app.{key}", str(value))

        try:
            yield
        except Exception as exc:
            span.record_exception(exc)
            store.append_event(
                event_type=event_type,
                status="error",
                dataset_id=dataset_id,
                duration_ms=(time.perf_counter() - start) * 1000,
                metadata=dict(metadata or {}, error=str(exc)),
            )
            raise
        else:
            store.append_event(
                event_type=event_type,
                status="success",
                dataset_id=dataset_id,
                duration_ms=(time.perf_counter() - start) * 1000,
                metadata=metadata,
            )

