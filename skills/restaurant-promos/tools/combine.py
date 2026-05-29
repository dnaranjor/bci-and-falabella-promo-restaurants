#!/usr/bin/env python3
"""Combine BCI and Falabella parsers into a unified restaurant table.

Filters for Santiago / Región Metropolitana, deduplicates by name,
and outputs a Markdown table with columns:
  Restaurant | Discount | Bank | Comuna | Ends | Details

Usage:
    python combine.py [--day SABADO]

Default day is Saturday if --day is omitted.
"""

import csv
import io
import os
import subprocess
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))

BCI_DAYS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
BF_DAYS_MAP = {
    "LUNES": "Lunes", "MARTES": "Martes", "MIERCOLES": "Miércoles",
    "JUEVES": "Jueves", "VIERNES": "Viernes", "SABADO": "Sábado",
    "DOMINGO": "Domingo",
}


def parse_args() -> tuple[str, str]:
    bci_day = "SABADO"
    raw = None
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--day" and i + 1 < len(argv):
            raw = argv[i + 1]
            break
        if a.startswith("--day="):
            raw = a.split("=", 1)[1]
            break
    if raw:
        upper = raw.upper()
        for d in BCI_DAYS:
            if upper == d or upper == d[:3]:
                bci_day = d
                break
        else:
            print(f"Invalid day '{raw}'. Use e.g. SABADO, VIERNES", file=sys.stderr)
            sys.exit(1)
    return bci_day, BF_DAYS_MAP[bci_day]


def is_santiago_rm(comuna: str) -> bool:
    return "Santiago" in comuna or "RM" in comuna or comuna in (
        "Vitacura", "Lo Barnechea", "Las Condes", "Providencia"
    )


def is_available_saturday(dias: str) -> bool:
    return "Sab" in dias or "Todos" in dias


def run_parser(script_name: str, day: str) -> str:
    path = os.path.join(TOOLS_DIR, script_name)
    result = subprocess.run(
        [sys.executable, path, "--day", day],
        capture_output=True, text=True, timeout=60,
    )
    return result.stdout


def parse_csv(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def extract_bci(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        comuna = r.get("Comuna", "")
        if not is_santiago_rm(comuna):
            continue
        out.append({
            "Restaurant": r["Restaurant"],
            "Discount": r["Discount"],
            "Bank": "Bci",
            "Comuna": comuna,
            "Ends": r["Ends"],
            "Details": r.get("Details", ""),
        })
    return out


def extract_falabella(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        comuna = r.get("Comuna", "")
        if not is_santiago_rm(comuna):
            continue
        dias = r.get("Cuando", "")
        if not is_available_saturday(dias):
            continue
        out.append({
            "Restaurant": r["Restaurant"],
            "Discount": r["Discount"],
            "Bank": r["TDC"],
            "Comuna": comuna,
            "Ends": r["Ends"],
            "Details": r.get("Details", ""),
        })
    return out


def deduplicate(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for r in rows:
        key = r["Restaurant"].lower().strip()
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def escape_md(text: str) -> str:
    return text.replace("|", "\\|")


def main():
    bci_day, bf_day = parse_args()

    bci_raw = run_parser("bci_parser.py", bci_day)
    bf_raw = run_parser("falabella_parser.py", bf_day)

    merged = extract_bci(parse_csv(bci_raw))
    merged.extend(extract_falabella(parse_csv(bf_raw)))

    merged = deduplicate(merged)
    merged.sort(key=lambda x: x["Restaurant"].lower())

    headers = ["Restaurant", "Discount", "Bank", "Comuna", "Ends", "Details"]
    sep = ["---"] * len(headers)
    out_lines = ["| " + " | ".join(headers) + " |"]
    out_lines.append("| " + " | ".join(sep) + " |")
    for r in merged:
        row = [escape_md(r.get(h, "")) for h in headers]
        out_lines.append("| " + " | ".join(row) + " |")
    sys.stdout.write("\n".join(out_lines) + "\n")


if __name__ == "__main__":
    main()
