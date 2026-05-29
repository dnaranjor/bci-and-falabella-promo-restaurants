# BCI & Falabella Promo Restaurants

**opencode skill** that fetches, parses, and combines Chilean restaurant promotions from BCI Plus (API) and Banco Falabella / CMR (SSR HTML).

## Usage

Install this skill via `skills.urls` in your `opencode.json`:

```json
{
  "skills": {
    "urls": ["https://raw.githubusercontent.com/dnaranjor/bci-and-falabella-promo-restaurants/main/.opencode/skills/restaurant-promos/SKILL.md"]
  }
}
```

Then ask opencode — the skill will ask you which day of the week you want:

> *"Show me restaurant deals from BCI and Falabella"*

Or specify the day explicitly:

> *"Fetch restaurant promotions for this Friday from both banks"*

### Standard output

Running `combine.py` outputs a formatted **Markdown table** (pipe-delimited)
ready for display or copying into documents.

### Direct script execution

Both parsers accept a `--day` argument. Default is Saturday.

```powershell
# Saturday (default) — unified output
python .opencode/skills/restaurant-promos/tools/combine.py

# Run individual parsers
python .opencode/skills/restaurant-promos/tools/bci_parser.py
python .opencode/skills/restaurant-promos/tools/falabella_parser.py

# Any other day
python .opencode/skills/restaurant-promos/tools/combine.py --day VIERNES
python .opencode/skills/restaurant-promos/tools/bci_parser.py --day VIERNES
python .opencode/skills/restaurant-promos/tools/falabella_parser.py --day Viernes
```

### Combine both sources for a given day

The standard entry point is `combine.py`, which merges both sources into a
unified table (Santiago/RM only, deduplicated, sorted):

```powershell
python .opencode/skills/restaurant-promos/tools/combine.py --day SABADO > restaurantes_sabado.csv
```

## Day name reference

| Day | BCI / combine (`--day`) | Falabella (`--day`) |
|-----|-------------------------|---------------------|
| Monday | LUNES | Lunes |
| Tuesday | MARTES | Martes |
| Wednesday | MIERCOLES | Miércoles |
| Thursday | JUEVES | Jueves |
| Friday | VIERNES | Viernes |
| Saturday | SABADO | Sábado |
| Sunday | DOMINGO | Domingo |

## Files

| File | Purpose |
|---|---|
| `.opencode/skills/restaurant-promos/SKILL.md` | Skill manifest & instructions |
| `.opencode/skills/restaurant-promos/tools/combine.py` | Merges both parsers → unified table (standard entry point) |
| `.opencode/skills/restaurant-promos/tools/bci_parser.py` | BCI Plus API → restaurants by day → CSV |
| `.opencode/skills/restaurant-promos/tools/falabella_parser.py` | Falabella SSR HTML → benefit cards by day → CSV |

## Standard output columns (combine.py)

`Restaurant`, `Discount`, `Bank`, `Comuna`, `Ends`, `Details`

Filtered to Santiago / Región Metropolitana, deduplicated by name.
`Details` shows deal-specific info (location, timing, constraints).

## Notes

- BCI API key is hardcoded (`fa981752762743668413b68821a43840`)
- If the BCI API is down, the script falls back to the last known cached data
- Falabella data is extracted from the Next.js SSR page via bracket-depth JSON parsing
