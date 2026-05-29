#!/usr/bin/env python3
"""Fetch and parse BCI restaurant promotions.

Uses the BCI Plus API with the same parameters as the frontend widget:
  GET /offers?itemsPorPagina=100&pagina=N
  Header: Ocp-Apim-Subscription-Key

Usage:
    python bci_parser.py [--day SABADO]
"""

import csv
import json
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime

API_URL = "https://api.bciplus.cl/bff-loyalty-beneficios/v1/offers"
API_KEYS = [
    "fa981752762743668413b68821a43840",
    "0d4842f95aa040c68920935ad43daba7",
]
ITEMS_PER_PAGE = 100
CATEGORY = "Restaurantes"

BCI_DAYS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]

COMUNA_MAP = {
    "vitacura": "Vitacura",
    "lo-barnechea": "Lo Barnechea",
    "las-condes": "Las Condes",
    "providencia": "Providencia",
    "nunoa": "Santiago (RM)",
    "la-florida": "Santiago (RM)",
    "maipu": "Santiago (RM)",
    "reina": "Santiago (RM)",
    "arica": "Arica",
    "iquique": "Iquique",
    "valparaiso": "Valpara\u00edso",
    "vina-del-mar": "Vi\u00f1a del Mar",
    "renaca": "Vi\u00f1a del Mar",
    "concepcion": "Concepci\u00f3n",
    "talca": "Talca",
    "valdivia": "Valdivia",
    "puerto-varas": "Puerto Varas",
}


def fetch_page(page: int, api_key: str) -> dict | None:
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    url = f"{API_URL}?itemsPorPagina={ITEMS_PER_PAGE}&pagina={page}"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "User-Agent": ua,
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"_error": e.code, "_body": body}
    except urllib.error.URLError as e:
        return {"_error": "connection", "_body": str(e.reason)}


def try_api(page: int) -> dict | None:
    for key in API_KEYS:
        result = fetch_page(page, key)
        if result is None:
            continue
        err = result.get("_error")
        if err:
            continue
        if "ofertas" in result:
            return result
    return None


def extract_comuna(slug: str) -> str:
    for key, comuna in COMUNA_MAP.items():
        if key in slug.lower():
            return comuna
    return "Santiago (RM)"


def format_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except (ValueError, AttributeError):
        return (iso_str or "")[:10]


def extract_restaurants(data: dict, day: str) -> list[dict]:
    restaurants = []
    for offer in data.get("ofertas", []):
        cats = [c["titulo"] for c in offer.get("categorias", [])]
        if CATEGORY not in cats:
            continue
        days = offer.get("scheduling", {}).get("dayRecurrence", [])
        if day not in days and days:
            continue
        name = offer.get("comercio", {}).get("nombre", "").strip() or offer.get("titulo", "").strip()
        discount = offer.get("beneficio", {}).get("discount", {}).get("porcentajeDescuento", 0)
        slug = offer.get("slug", "")
        title = offer.get("titulo", "")
        rest_data = {
            "Restaurant": name,
            "Discount": f"{discount}%",
            "TDC": "Bci",
            "Cuando": day.capitalize(),
            "Comuna": extract_comuna(slug),
            "Ends": format_date(offer.get("fechaTermino", "")),
            "Details": title,
        }
        if rest_data not in restaurants:
            restaurants.append(rest_data)
    return restaurants


def parse_args() -> str:
    day = "SABADO"
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
        for bci_day in BCI_DAYS:
            if raw.upper() == bci_day or raw.upper() == bci_day[:3]:
                day = bci_day
                break
        else:
            print(f"Invalid day '{raw}'. Choose from: {', '.join(BCI_DAYS)}", file=sys.stderr)
            sys.exit(1)
    return day


def main():
    day = parse_args()
    all_restaurants = []

    data = try_api(1)
    if data and "ofertas" in data:
        pag = data.get("paginado", {})
        all_restaurants.extend(extract_restaurants(data, day))
        total_pages = pag.get("totalPaginas", 1)
        for page in range(2, total_pages + 1):
            d = try_api(page)
            if d and "ofertas" in d:
                all_restaurants.extend(extract_restaurants(d, day))

    if not all_restaurants:
        print("BCI API unavailable. No restaurant data found.", file=sys.stderr)

    fieldnames = ["Restaurant", "Discount", "TDC", "Cuando", "Comuna", "Ends", "Details"]
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    for r in sorted(all_restaurants, key=lambda x: x["Restaurant"]):
        writer.writerow(r)


if __name__ == "__main__":
    main()
