#!/usr/bin/env python3
"""Build a slope-chart-ready wide CSV from sheet 1 of 04_slope_chart_ranking.xlsx."""

from __future__ import annotations

import argparse
import csv
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def col_to_idx(col_ref: str) -> int:
    value = 0
    for ch in col_ref:
        if ch.isalpha():
            value = (value * 26) + (ord(ch.upper()) - 64)
    return value - 1


def read_cell_value(cell: ET.Element, shared_strings: List[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        inline = cell.find(f"{{{NS_MAIN}}}is")
        if inline is None:
            return ""
        return "".join((t.text or "") for t in inline.iter(f"{{{NS_MAIN}}}t"))

    value = cell.find(f"{{{NS_MAIN}}}v")
    if value is None or value.text is None:
        return ""

    raw = value.text
    if cell_type == "s":
        return shared_strings[int(raw)] if raw.isdigit() else raw
    return raw


def resolve_sheet_path(xlsx: zipfile.ZipFile, sheet_index: int) -> str:
    workbook = ET.fromstring(xlsx.read("xl/workbook.xml"))
    sheets = workbook.find(f"{{{NS_MAIN}}}sheets")
    if sheets is None:
        raise ValueError("Nessun foglio trovato nel file Excel.")
    if sheet_index >= len(sheets):
        raise ValueError(f"Indice foglio non valido: {sheet_index}")

    rels = ET.fromstring(xlsx.read("xl/_rels/workbook.xml.rels"))
    rid_to_target = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
    sheet = sheets[sheet_index]
    rel_id = sheet.attrib.get(f"{{{NS_REL}}}id")
    if not rel_id or rel_id not in rid_to_target:
        raise ValueError("Impossibile risolvere il path del foglio.")

    target = rid_to_target[rel_id]
    if target.startswith("/"):
        return target.lstrip("/")
    if target.startswith("xl/"):
        return target
    return f"xl/{target}"


def read_shared_strings(xlsx: zipfile.ZipFile) -> List[str]:
    shared_path = "xl/sharedStrings.xml"
    if shared_path not in xlsx.namelist():
        return []

    sst = ET.fromstring(xlsx.read(shared_path))
    return ["".join((t.text or "") for t in si.iter(f"{{{NS_MAIN}}}t")) for si in sst.findall(f"{{{NS_MAIN}}}si")]


def read_first_sheet_rows(xlsx_path: Path) -> List[Dict[str, str]]:
    with zipfile.ZipFile(xlsx_path) as xlsx:
        shared_strings = read_shared_strings(xlsx)
        sheet_path = resolve_sheet_path(xlsx, sheet_index=0)
        sheet_xml = ET.fromstring(xlsx.read(sheet_path))

    sheet_data = sheet_xml.find(f"{{{NS_MAIN}}}sheetData")
    if sheet_data is None:
        raise ValueError("Il primo foglio non contiene dati.")

    matrix: List[List[str]] = []
    max_col = -1
    for row in sheet_data.findall(f"{{{NS_MAIN}}}row"):
        values_by_col: Dict[int, str] = {}
        for cell in row.findall(f"{{{NS_MAIN}}}c"):
            ref = cell.attrib.get("r", "A1")
            col_ref = "".join(ch for ch in ref if ch.isalpha())
            col_idx = col_to_idx(col_ref)
            values_by_col[col_idx] = read_cell_value(cell, shared_strings).strip()
            max_col = max(max_col, col_idx)
        matrix.append([values_by_col.get(i, "") for i in range(max_col + 1)])

    if not matrix:
        return []

    header = [h.strip() for h in matrix[0]]
    rows: List[Dict[str, str]] = []
    for row in matrix[1:]:
        if len(row) < len(header):
            row.extend([""] * (len(header) - len(row)))
        item = {header[i]: row[i] for i in range(len(header))}
        if any(v for v in item.values()):
            rows.append(item)
    return rows


def to_float(value: str) -> float:
    text = (value or "").strip().replace(",", ".")
    if not text:
        return 0.0
    return float(text)


def format_metric(value: float, metric: str) -> str:
    if metric in {"revenue_eur", "impression"}:
        return str(int(round(value)))
    return f"{value:.2f}"


def build_wide(rows: List[Dict[str, str]], metric: str) -> Tuple[List[str], List[List[str]]]:
    available_cols = set(rows[0].keys()) if rows else set()
    if metric not in available_cols:
        raise ValueError(f"Metrica '{metric}' non trovata. Colonne disponibili: {', '.join(sorted(available_cols))}")

    value_map: Dict[Tuple[str, str], float] = defaultdict(float)
    testate = set()
    periodi = set()

    for row in rows:
        testata = (row.get("testata", "") or "").strip()
        trimestre = (row.get("trimestre", "") or "").strip()
        val = to_float(row.get(metric, "0"))
        if not testata or not trimestre:
            continue
        value_map[(testata, trimestre)] += val
        testate.add(testata)
        periodi.add(trimestre)

    ordered_periodi = sorted(periodi, key=lambda p: (p.split("-")[1], p.split("-")[0]))
    ordered_testate = sorted(testate)

    header = ["Testata"] + ordered_periodi
    out_rows: List[List[str]] = []
    for t in ordered_testate:
        row = [t]
        for p in ordered_periodi:
            row.append(format_metric(value_map.get((t, p), 0.0), metric))
        out_rows.append(row)
    return header, out_rows


def write_csv(path: Path, header: List[str], rows: List[List[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Converte il primo foglio Excel in CSV wide per slope chart Flourish."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("04_slope_chart_ranking.xlsx"),
        help="Percorso file Excel di input.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("slope_ready.csv"),
        help="Percorso file CSV di output.",
    )
    parser.add_argument(
        "-m",
        "--metric",
        default="revenue_eur",
        help="Metrica da visualizzare (es: revenue_eur, cpm_medio, fill_rate_pct, viewability_pct, impression).",
    )
    args = parser.parse_args()

    rows = read_first_sheet_rows(args.input)
    if not rows:
        raise ValueError("Nessuna riga trovata nel primo foglio.")
    if "testata" not in rows[0] or "trimestre" not in rows[0]:
        raise ValueError("Colonne richieste mancanti: testata e/o trimestre.")

    header, out_rows = build_wide(rows, metric=args.metric)
    write_csv(args.output, header, out_rows)
    print(f"CSV creato: {args.output} (metrica: {args.metric})")


if __name__ == "__main__":
    main()
