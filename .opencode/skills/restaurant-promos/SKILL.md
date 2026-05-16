---
name: restaurant-promos
description: >
  Use ONLY when the user asks about Chilean restaurant promotions, discounts,
  BCI Plus, Banco Falabella CMR, restaurantes con descuento, or building/
  updating a unified table of restaurant deals from both sources.
  Keywords: BCI, Bci, Banco Falabella, CMR, restaurantes, descuentos,
  promotions, parser, scrape.
  Do NOT use for general shopping, travel, or non-restaurant benefits.
---

# Restaurant Promos (Chile)

Tools to fetch, parse, and combine Chilean restaurant promotions from **BCI
Plus** (API) and **Banco Falabella / CMR** (SSR HTML). Designed for the
`restaurant-promos` skill directory at
`~/.config/opencode/skills/restaurant-promos/`.

## Scripts

### `bci_parser.py`
Fetches the BCI Plus offers API, filters for `Restaurantes` category with
`SABADO` day recurrence, and writes normalized CSV to stdout.

**Usage:**
```
python ~/.config/opencode/skills/restaurant-promos/bci_parser.py
```

**Output columns:** `Restaurant`, `Discount`, `TDC`, `Cuando`, `Comuna`, `Ends`

- API key is hardcoded (fa981752762743668413b68821a43840)
- Paginates through all pages (100 items/page)
- Comuna extracted from the offer `slug` field
- **Fallback**: if the live API is unavailable (HTTP 500), outputs the last
  known cached results (4 BCI restaurants from Jan 2026 research) as a
  stopgap until the API recovers

### `falabella_parser.py`
Fetches the Banco Falabella descuentos/restaurantes page (Next.js SSR),
extracts the `benefitCardsData` JSON array embedded in
`self.__next_f.push(...)` payloads, filters for cards available on Sábado,
and writes CSV to stdout.

**Usage:**
```
python ~/.config/opencode/skills/restaurant-promos/falabella_parser.py
```

**Output columns:** `Restaurant`, `Discount`, `TDC`, `Cuando`, `Comuna`,
`Ends`, `TipoComida`

- Parses escaped JSON via bracket-depth counting
- Deduplicates by benefitTitle
- Detects CMR Elite vs regular CMR
- Region → Comuna mapping: RM → "Santiago (RM)", RM+Valparaíso →
  "RM / Valparaiso", Los Lagos → "Region de Los Lagos"

### Combining both into the full table

```powershell
$bci = python ~/.config/opencode/skills/restaurant-promos/bci_parser.py 2>$null
$bf  = python ~/.config/opencode/skills/restaurant-promos/falabella_parser.py 2>$null
($bci.Trim() + "`n" + $bf.Trim()) | Set-Content -Path "C:\Users\dnara\OneDrive\Desktop\restaurantes_descuentos.csv"
```

Or from Python directly:

```python
import subprocess, sys
base = r"C:\Users\dnara\.config\opencode\skills\restaurant-promos"
bci = subprocess.run([sys.executable, f"{base}\\bci_parser.py"],
    capture_output=True, text=True).stdout
bf  = subprocess.run([sys.executable, f"{base}\\falabella_parser.py"],
    capture_output=True, text=True).stdout
with open("restaurantes.csv", "w", encoding="utf-8") as f:
    f.write(bci.strip() + "\n" + bf.strip())
```

## Enrichment steps (performed manually)

After generating the combined CSV:

1. **TipoComida** — fill via restaurant description/name research
   (e.g., `"India"`, `"Peruana"`, `"Japonesa"`, `"Parrilla"`, etc.)
2. **Recomendacion** — research prices, ratings, atmosphere; write a
   recommendation per restaurant with budget estimates
3. **Ranking** — sort rows 1–N by suitability for the user's preferences
   (couple late 50s, budget CLP 20K–25K pp incl. alcohol, quality dining,
   adventurous palate)

## Cached reference data

- Full 32-row table with TipoComida and Recomendacion is kept in the
  conversation summary (in-memory). Ask the assistant for the current table.
- Raw source data and previous PowerShell parsing scripts are in:
  `C:\Users\dnara\AppData\Local\Temp\opencode\`
- Extracted BF cards JSON: `cards_full.json`
