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

## Interactive use

When this skill is triggered, first **ask the user which day of the week**
they want to query (e.g., "Sábado", "Viernes", "Lunes"). Then run the
combine script which merges both sources and outputs a unified table.

### Standard output table

| Restaurant | Discount | Bank | Comuna | Ends | Details |
|---|---|---|---|---|---|

Filtered to Santiago / Región Metropolitana, deduplicated by restaurant name,
sorted alphabetically. The `Bank` column shows `Bci`, `CMR`, or `CMR Elite`.
The `Details` column shows deal-specific info (location, timing, constraints).

## Scripts

### `bci_parser.py`
Fetches the BCI Plus offers API, filters for `Restaurantes` category matching
the requested day, and writes normalized CSV to stdout.

**Usage:**
```
python bci_parser.py --day SABADO
```

**Output columns:** `Restaurant`, `Discount`, `TDC`, `Cuando`, `Comuna`, `Ends`

- Accepts `--day` with full name (`SABADO`) or 3-letter abbreviation (`SAB`)
- Tries two known API keys
- Paginates through all pages (100 items/page via `itemsPorPagina=100&pagina=N`)
- Comuna extracted from the offer `slug` field
- Uses the same API parameters as the BCI frontend Vue.js widget
- Previously returned HTTP 500 due to incorrect parameter format (`page`/`size`
  instead of `pagina`/`itemsPorPagina`)

### `falabella_parser.py`
Fetches the Banco Falabella descuentos/restaurantes page (Next.js SSR),
extracts the `benefitCardsData` JSON array embedded in
`self.__next_f.push(...)` payloads, filters for cards available on the
requested day, and writes CSV to stdout.

**Usage:**
```
python falabella_parser.py --day Sabado
```

**Output columns:** `Restaurant`, `Discount`, `TDC`, `Cuando`, `Comuna`,
`Ends`, `TipoComida`

- Accepts `--day` in Spanish (`Sabado`, `Viernes`, `Lunes`, etc.)
- Parses escaped JSON via bracket-depth counting
- Deduplicates by benefitTitle
- Detects CMR Elite vs regular CMR
- Region to Comuna mapping: RM "Santiago (RM)", RM+Valparaíso
  "RM / Valparaiso", 10+ regions "Nacional"

### Combining both for a given day (using combine.py)

```powershell
python .opencode/skills/restaurant-promos/tools/combine.py --day SABADO > restaurantes_sabado.csv
```

From Python directly:

```python
import subprocess, sys
base = r"C:\Users\dnara\.config\opencode\skills\restaurant-promos\tools"
day = "SABADO"
result = subprocess.run([sys.executable, f"{base}\\combine.py", "--day", day],
    capture_output=True, text=True)
with open(f"restaurantes_{day.lower()}.csv", "w", encoding="utf-8") as f:
    f.write(result.stdout)
```

### `combine.py` (standard entry point)

Merges both parsers into a Markdown table. Filters to Santiago /
Región Metropolitana, deduplicates by name, sorts alphabetically.

**Usage:**
```
python combine.py --day SABADO
```

**Output columns:** `Restaurant`, `Discount`, `Bank`, `Comuna`, `Ends`, `Details`

- Accepts `--day` with BCI-style day names (e.g., `SABADO`, `VIERNES`)
- Runs both parsers internally, then filters, deduplicates, and merges
- `Bank` column shows `Bci`, `CMR`, or `CMR Elite`
- Output is a formatted Markdown table (pipe-delimited)

## Enrichment steps (performed manually after fetching raw data)

1. **TipoComida** — fill via restaurant description/name research
   (e.g., "India", "Peruana", "Japonesa", "Parrilla", etc.)
2. **Recomendacion** — research prices, ratings, atmosphere; write a
   recommendation per restaurant with budget estimates
3. **Ranking** — sort rows 1-N by suitability for the user's profile

## Day name reference

| Day | BCI (`--day`) | Falabella (`--day`) |
|-----|---------------|---------------------|
| Monday | LUNES | Lunes |
| Tuesday | MARTES | Martes |
| Wednesday | MIERCOLES | Miércoles |
| Thursday | JUEVES | Jueves |
| Friday | VIERNES | Viernes |
| Saturday | SABADO | Sábado |
| Sunday | DOMINGO | Domingo |
