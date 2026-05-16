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

Then ask opencode:

> *"Fetch the latest restaurant deals from BCI and Falabella for this Saturday"*

Or run the scripts directly:

```powershell
python .opencode/skills/restaurant-promos/bci_parser.py
python .opencode/skills/restaurant-promos/falabella_parser.py
```

## Files

| File | Purpose |
|---|---|
| `.opencode/skills/restaurant-promos/SKILL.md` | Skill manifest & instructions |
| `.opencode/skills/restaurant-promos/bci_parser.py` | BCI Plus API → restaurants on Sábado → CSV |
| `.opencode/skills/restaurant-promos/falabella_parser.py` | Falabella SSR HTML → benefit cards on Sábado → CSV |

## Output columns

`Restaurant`, `Discount`, `TDC`, `Cuando`, `Comuna`, `Ends`, `TipoComida`

## Notes

- BCI API key is hardcoded (`fa981752762743668413b68821a43840`)
- If the BCI API is down, the script falls back to the last known cached data
- Falabella data is extracted from the Next.js SSR page via bracket-depth JSON parsing
