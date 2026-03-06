#!/usr/bin/env python3
"""Build a scatter-ready CSV from sheet 1 of 03_scatter_cpm_fillrate.xlsx.

Output columns:
- Testata
- CPM Medio (€) -> weighted average by impression_totali
- Fill Rate (%) -> weighted average by impression_totali
- Revenue (€) -> sum of revenue_eur (rounded to int)
- Mese
"""

from __future__ import annotations

import argparse
import csv
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from xml.etree import ElementTree as ET

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
IT_MONTH_TO_NUM = {
    "gen": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "mag": 5,
    "giu": 6,
    "lug": 7,
    "ago": 8,
    "set": 9,
    "ott": 10,
    "nov": 11,
    "dic": 12,
}


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


def parse_month_key(month_label: str) -> date:
    text = (month_label or "").strip()
    lower = text.lower()
    month_txt, year_txt = lower.split("-")
    return date(int(year_txt), IT_MONTH_TO_NUM[month_txt], 1)


def to_float(value: str) -> float:
    text = (value or "").strip().replace(",", ".")
    if not text:
        return 0.0
    return float(text)


def build_scatter_rows(rows: Iterable[Dict[str, str]]) -> List[List[str]]:
    # Key: (testata, mese)
    agg: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(
        lambda: {"imp": 0.0, "cpm_x_imp": 0.0, "fill_x_imp": 0.0, "rev": 0.0}
    )

    for row in rows:
        testata = (row.get("testata", "") or "").strip()
        mese = (row.get("mese", "") or "").strip()
        imp = to_float(row.get("impression_totali", "0"))
        cpm = to_float(row.get("cpm_medio", "0"))
        fill = to_float(row.get("fill_rate_pct", "0"))
        rev = to_float(row.get("revenue_eur", "0"))

        if not testata or not mese:
            continue

        bucket = agg[(testata, mese)]
        bucket["imp"] += imp
        bucket["cpm_x_imp"] += cpm * imp
        bucket["fill_x_imp"] += fill * imp
        bucket["rev"] += rev

    ordered_keys = sorted(agg.keys(), key=lambda k: (parse_month_key(k[1]), k[0]))
    out_rows: List[List[str]] = []

    for testata, mese in ordered_keys:
        b = agg[(testata, mese)]
        imp = b["imp"]
        cpm_weighted = (b["cpm_x_imp"] / imp) if imp else 0.0
        fill_weighted = (b["fill_x_imp"] / imp) if imp else 0.0
        revenue = int(round(b["rev"]))

        out_rows.append(
            [
                testata,
                f"{cpm_weighted:.2f}",
                f"{fill_weighted:.1f}",
                str(revenue),
                mese,
            ]
        )

    return out_rows


def write_csv(path: Path, rows: List[List[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Testata", "CPM Medio (€)", "Fill Rate (%)", "Revenue (€)", "Mese"])
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Converte il primo foglio Excel in CSV per scatter Flourish."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("03_scatter_cpm_fillrate.xlsx"),
        help="Percorso file Excel di input.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("scatter_ready.csv"),
        help="Percorso file CSV di output.",
    )
    args = parser.parse_args()

    rows = read_first_sheet_rows(args.input)
    if not rows:
        raise ValueError("Nessuna riga trovata nel primo foglio.")

    required = {"mese", "testata", "cpm_medio", "fill_rate_pct", "impression_totali", "revenue_eur"}
    missing = [c for c in required if c not in rows[0]]
    if missing:
        raise ValueError(f"Colonne mancanti nel primo foglio: {', '.join(missing)}")

    out_rows = build_scatter_rows(rows)
    write_csv(args.output, out_rows)
    print(f"CSV creato: {args.output}")


if __name__ == "__main__":
    main()
