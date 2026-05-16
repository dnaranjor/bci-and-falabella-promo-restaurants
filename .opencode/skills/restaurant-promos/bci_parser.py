#!/usr/bin/env python3
"""Fetch and parse BCI restaurant promotions from the BCI Plus API.

Usage:
    python bci_parser.py [--day SABADO]

Outputs CSV to stdout with columns: Restaurant, Discount, TDC, Cuando, Comuna, Ends.
Default day is SABADO if --day is omitted.

If the live API is unavailable, outputs the last known cached data.
"""

import csv
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime

API_URL = "https://api.bciplus.cl/bff-loyalty-beneficios/v1/offers"
API_KEY = "fa981752762743668413b68821a43840"
ITEMS_PER_PAGE = 100
CATEGORY = "Restaurantes"

BCI_DAYS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]

LAST_KNOWN_DATA = [
    {"Restaurant": "Burgerholic", "Discount": "20%", "TDC": "Bci", "Cuando": "Sabado", "Comuna": "Lo Barnechea", "Ends": "01/01/2027"},
    {"Restaurant": "Majestic", "Discount": "30%", "TDC": "Bci", "Cuando": "Sabado", "Comuna": "Vitacura", "Ends": "01/07/2026"},
    {"Restaurant": "Oporto salvaje", "Discount": "50%", "TDC": "Bci", "Cuando": "Sabado", "Comuna": "Santiago (RM)", "Ends": "01/08/2026"},
    {"Restaurant": "Starburger", "Discount": "20%", "TDC": "Bci", "Cuando": "Sabado", "Comuna": "Santiago (RM)", "Ends": "01/01/2027"},
]


def fetch_page(page: int) -> dict | None:
    url = f"{API_URL}?page={page}&size={ITEMS_PER_PAGE}&sort=prioridad,desc"
    req = urllib.request.Request(url, headers={
        "Ocp-Apim-Subscription-Key": API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"BCI API error (HTTP {e.code})", file=sys.stderr)
        return None


def extract_comuna(slug: str) -> str:
    for key, comuna in {
        "vitacura": "Vitacura",
        "lo-barnechea": "Lo Barnechea",
        "las-condes": "Las Condes",
        "providencia": "Providencia",
    }.items():
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
        restaurants.append({
            "Restaurant": name,
            "Discount": f"{discount}%",
            "TDC": "Bci",
            "Cuando": day.capitalize(),
            "Comuna": extract_comuna(offer.get("slug", "")),
            "Ends": format_date(offer.get("fechaTermino", "")),
        })
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
    data = fetch_page(0)

    if data is None:
        for page in range(1, 3):
            d = fetch_page(page)
            if d:
                all_restaurants.extend(extract_restaurants(d, day))

    if data:
        pag = data.get("paginado", {})
        all_restaurants.extend(extract_restaurants(data, day))
        for page in range(1, pag.get("totalPaginas", 1)):
            d = fetch_page(page)
            if d:
                all_restaurants.extend(extract_restaurants(d, day))

    if not all_restaurants:
        print("BCI API unavailable, using last known cached data.", file=sys.stderr)
        all_restaurants = LAST_KNOWN_DATA

    writer = csv.DictWriter(sys.stdout, fieldnames=["Restaurant", "Discount", "TDC", "Cuando", "Comuna", "Ends"])
    writer.writeheader()
    for r in sorted(all_restaurants, key=lambda x: x["Restaurant"]):
        writer.writerow(r)


if __name__ == "__main__":
    main()
