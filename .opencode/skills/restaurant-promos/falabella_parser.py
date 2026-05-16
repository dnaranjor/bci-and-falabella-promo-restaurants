#!/usr/bin/env python3
"""Fetch and parse Banco Falabella restaurant promotions from SSR HTML."""

import csv
import json
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime

BF_URL = "https://www.bancofalabella.cl/descuentos/restaurantes"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def extract_benefit_cards(html: str) -> list[dict]:
    idx = html.find("benefitCardsData")
    if idx == -1:
        raise ValueError("benefitCardsData not found in HTML")

    colon_idx = html.find(":[", idx)
    if colon_idx == -1:
        raise ValueError("'':['' not found after benefitCardsData")

    arr_start = colon_idx + 1
    depth = 0
    in_str = False
    arr_end = -1
    i = arr_start
    while i < len(html):
        ch = html[i]
        prev = html[i - 1] if i > arr_start else ""
        if ch == '"' and prev != "\\":
            in_str = not in_str
        if not in_str:
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    arr_end = i
                    break
        i += 1

    if arr_end == -1:
        raise ValueError("Failed to find matching closing bracket")

    raw = html[arr_start : arr_end + 1]
    raw = raw.replace('\\"', '"').replace("\\/", "/").replace("\\n", " ")
    return json.loads(raw)


def format_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except (ValueError, AttributeError):
        return iso_str[:10] if iso_str else ""


def has_sabado(discount_days: list | None) -> bool:
    if not discount_days:
        return False
    for d in discount_days:
        dl = d.lower()
        if "sab" in dl or "sáb" in dl:
            return True
    return False


def format_days(discount_days: list | None) -> str:
    if not discount_days:
        return ""
    days = []
    for d in discount_days:
        dl = d.lower()
        if "lun" in dl:
            days.append("Lun")
        elif "mar" in dl:
            days.append("Mar")
        elif "mie" in dl or "mié" in dl or "miér" in dl:
            days.append("Mie")
        elif "jue" in dl:
            days.append("Jue")
        elif "vie" in dl:
            days.append("Vie")
        elif "sab" in dl or "sáb" in dl:
            days.append("Sab")
        elif "dom" in dl:
            days.append("Dom")
        else:
            days.append(d)
    return ", ".join(dict.fromkeys(days))


DAYS_ORDER = {"Lun": 0, "Mar": 1, "Mie": 2, "Jue": 3, "Vie": 4, "Sab": 5, "Dom": 6}
ALL_DAYS = {"Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"}


def normalize_cuando(days_str: str) -> str:
    if not days_str:
        return ""
    unique = [d.strip() for d in days_str.split(",") if d.strip()]
    unique = list(dict.fromkeys(unique))
    if not unique:
        return ""
    if set(unique) == ALL_DAYS:
        return "Todos los dias"
    unique.sort(key=lambda d: DAYS_ORDER.get(d, 99))
    return ", ".join(unique)


def region_to_comuna(regions: list | None) -> str:
    if not regions:
        return "Santiago (RM)"
    if len(regions) >= 10:
        return "Nacional"
    joined = "; ".join(regions)
    if "Metropolitana" in joined and "Valparaíso" in joined:
        return "RM / Valparaiso"
    if "Metropolitana" in joined:
        return "Santiago (RM)"
    if "Los Lagos" in joined:
        return "Region de Los Lagos"
    return joined


def simplify_card(card: dict) -> str:
    elite_tag = card.get("benefitCard", {}).get("eliteTag", False)
    if elite_tag:
        return "CMR Elite"
    return "CMR"


def main():
    html = fetch_html(BF_URL)
    cards = extract_benefit_cards(html)

    writer = csv.DictWriter(sys.stdout, fieldnames=[
        "Restaurant", "Discount", "TDC", "Cuando", "Comuna", "Ends", "TipoComida"
    ])
    writer.writeheader()

    seen = set()
    for card in cards:
        benefit_title = card.get("benefitTitle", "")
        if not benefit_title:
            benefit_title = card.get("benefitCard", {}).get("title", "").replace("Descuento en Restaurante ", "").strip()
        if not benefit_title:
            continue

        discount_days = card.get("benefitCard", {}).get("discountDays", [])
        if not has_sabado(discount_days):
            continue

        dedup_key = benefit_title.lower().strip()
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        discount = card.get("discount", 0)
        end_date = format_date(card.get("benefitCard", {}).get("endDate", ""))
        regions = card.get("region", [])

        days_raw = format_days(discount_days)
        cuando = normalize_cuando(days_raw)

        writer.writerow({
            "Restaurant": benefit_title,
            "Discount": f"{discount}%",
            "TDC": simplify_card(card),
            "Cuando": cuando,
            "Comuna": region_to_comuna(regions),
            "Ends": end_date,
            "TipoComida": "",
        })


if __name__ == "__main__":
    main()
