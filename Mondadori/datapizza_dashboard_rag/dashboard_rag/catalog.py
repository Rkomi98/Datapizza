from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .config import Settings


MONTH_PATTERN = re.compile(r"^(gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)-\d{4}$", re.IGNORECASE)
QUARTER_PATTERN = re.compile(r"^q[1-4]-\d{4}$", re.IGNORECASE)


@dataclass(frozen=True)
class DatasetEntry:
    name: str
    path: Path
    dataset_id: str
    kind: str
    description: str
    columns: List[str]

    @property
    def label(self) -> str:
        return f"{self.name} [{self.kind}]"


def _read_headers(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return [value.strip() for value in next(reader, [])]


def _build_dataset_id(path: Path) -> str:
    digest = hashlib.md5(str(path.resolve()).encode("utf-8")).hexdigest()[:8]
    slug = re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_")
    return f"{slug}_{digest}"


def _infer_kind(headers: List[str]) -> str:
    header_set = set(headers)
    lower_headers = [header.lower() for header in headers]

    if {"Source", "Target", "Value"}.issubset(header_set):
        return "sankey"
    if {"Testata", "CPM Medio (€)", "Fill Rate (%)", "Revenue (€)", "Mese"}.issubset(header_set):
        return "scatter"
    if headers and headers[0] == "Testata" and any(MONTH_PATTERN.match(header) for header in lower_headers[1:]):
        return "bar_chart_race"
    if headers and headers[0] == "Testata" and any(QUARTER_PATTERN.match(header) for header in lower_headers[1:]):
        return "slope"
    return "generic"


def _describe_kind(kind: str) -> str:
    descriptions = {
        "sankey": "Flussi Source/Target/Value per view tipo sankey.",
        "scatter": "KPI mensili per testata con CPM, fill rate e revenue.",
        "bar_chart_race": "Serie temporale wide con revenue cumulativa per testata.",
        "slope": "Confronto wide per trimestre tra testate.",
        "generic": "CSV generico non riconosciuto automaticamente.",
    }
    return descriptions.get(kind, "CSV generico.")


def discover_datasets(settings: Settings) -> List[DatasetEntry]:
    candidates = {}

    for path in settings.repo_dir.glob("*.csv"):
        candidates[path.resolve()] = path
    for path in settings.datasets_dir.rglob("*.csv"):
        candidates[path.resolve()] = path

    datasets: List[DatasetEntry] = []
    for path in sorted(candidates.values(), key=lambda item: item.name.lower()):
        headers = _read_headers(path)
        kind = _infer_kind(headers)
        datasets.append(
            DatasetEntry(
                name=path.name,
                path=path,
                dataset_id=_build_dataset_id(path),
                kind=kind,
                description=_describe_kind(kind),
                columns=headers,
            )
        )

    return datasets

