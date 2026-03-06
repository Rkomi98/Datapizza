#!/usr/bin/env python3
"""Convert the first sheet of an XLSX file into a Bar Chart Race-ready CSV.

Input sheet (long format) expected columns:
- mese_anno
- testata
- revenue_eur

Output CSV (wide format):
- first column: Testata
- next columns: ordered periods
- values: cumulative revenue by period
"""

from __future__ import annotations

import argparse
import csv
import re
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from xml.etree import ElementTree as ET

# Queste due costanti definiscono i namespace XML usati nei file XLSX:
# - NS_MAIN: Namespace principale per gli elementi dello spreadsheet (celle, righe, fogli, ecc.).
# - NS_REL: Namespace utilizzato per le relazioni tra i file interni (collega risorse nel pacchetto).
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
NUM_TO_IT_MONTH = {v: k.capitalize() for k, v in IT_MONTH_TO_NUM.items()}


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
    values: List[str] = []
    for si in sst.findall(f"{{{NS_MAIN}}}si"):
        values.append("".join((t.text or "") for t in si.iter(f"{{{NS_MAIN}}}t")))
    return values


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
            cell_ref = cell.attrib.get("r", "A1")
            col_ref = "".join(ch for ch in cell_ref if ch.isalpha())
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


def parse_period(label: str) -> date:
    text = (label or "").strip()
    lower = text.lower()

    match_it = re.fullmatch(r"([a-z]{3})[-/ ](\d{4})", lower)
    if match_it:
        month_txt, year_txt = match_it.groups()
        if month_txt in IT_MONTH_TO_NUM:
            return date(int(year_txt), IT_MONTH_TO_NUM[month_txt], 1)

    match_iso = re.fullmatch(r"(\d{4})[-/](\d{1,2})", lower)
    if match_iso:
        year_txt, month_txt = match_iso.groups()
        return date(int(year_txt), int(month_txt), 1)

    raise ValueError(f"Formato mese_anno non riconosciuto: '{label}'")


def period_to_label(period: date) -> str:
    return f"{NUM_TO_IT_MONTH[period.month]}-{period.year}"


def to_float(value: str) -> float:
    text = (value or "").strip().replace(",", ".")
    if not text:
        return 0.0
    return float(text)


def build_wide_cumulative(rows: Iterable[Dict[str, str]]) -> Tuple[List[str], List[List[str]]]:
    monthly_revenue: Dict[Tuple[str, date], float] = defaultdict(float)
    testate_set = set()
    periods_set = set()

    for row in rows:
        period = parse_period(row.get("mese_anno", ""))
        testata = (row.get("testata", "") or "").strip()
        revenue = to_float(row.get("revenue_eur", "0"))

        if not testata:
            continue

        monthly_revenue[(testata, period)] += revenue
        testate_set.add(testata)
        periods_set.add(period)

    periods = sorted(periods_set)
    testate = sorted(testate_set)

    header = ["Testata"] + [period_to_label(p) for p in periods]
    data: List[List[str]] = []

    for testata in testate:
        cumulative = 0.0
        row = [testata]
        for period in periods:
            cumulative += monthly_revenue.get((testata, period), 0.0)
            row.append(str(int(round(cumulative))))
        data.append(row)

    return header, data


def write_csv(path: Path, header: List[str], rows: List[List[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Converte il primo foglio Excel in CSV wide cumulativo per Bar Chart Race."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("01_bar_chart_race_revenue.xlsx"),
        help="Percorso file Excel di input.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("bar_chart_race_ready.csv"),
        help="Percorso file CSV di output.",
    )
    args = parser.parse_args()

    rows = read_first_sheet_rows(args.input)
    if not rows:
        raise ValueError("Nessuna riga trovata nel primo foglio.")

    required = {"mese_anno", "testata", "revenue_eur"}
    missing = [c for c in required if c not in rows[0]]
    if missing:
        raise ValueError(f"Colonne mancanti nel primo foglio: {', '.join(missing)}")

    header, out_rows = build_wide_cumulative(rows)
    write_csv(args.output, header, out_rows)
    print(f"CSV creato: {args.output}")


if __name__ == "__main__":
    main()
