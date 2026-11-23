# Sana Financial Operations

One dashboard for Sana's whole business: Sana (Trybe), the restaurant (Silverware POS),
staffing (Push) and profitability (general ledger), with a lean Strategy tab for the winter
outlook and scenarios.

It exists in two places, built from the same page:

| Where | What | Who sees it |
|---|---|---|
| Claude artifact "Sana Financial Operations" | Live master. Reads copies of the source dashboards' data files. | Whoever Col shares it with in Claude |
| GitHub Pages (`docs/index.html`) | Password-protected snapshot for partners. AES-256-GCM, decrypted in the browser. | Anyone with the link **and** the password |

## Layout

- `src/index.html` — the page (tabs: Overview, Sana, Restaurant, Staffing, Strategy). Same file as the artifact's `files/index.html`.
- `data/*.csv` — snapshot data for the GitHub copy. Not committed; `data/bundle.enc` holds them encrypted with the page password.
- `tools/shim.js` — small stand-in for the Claude dashboard runtime so the page runs as a static site.
- `tools/build.py` — builds `docs/index.html` (encrypted) and `dist/preview.html` (local, ignored).
- `tools/smoke.py` — headless check: opens every tab at desktop and phone width and reports errors.
- `SYNC.md` — how the master follows the four source dashboards.

## Build

```
npm install            # d3
SFO_PASSWORD='…' python3 tools/build.py
python3 tools/smoke.py
```

The password is never stored in the repo. The repo can be public (GitHub Pages needs that on a
free plan): the page and the data bundle are both encrypted, and the source code holds no figures.

## Data sources

| Dataset | Source dashboard | File |
|---|---|---|
| `trybe_monthly`, `founding` | Sana Trybe: bookings, occupancy and buying patterns | `monthly.csv`, `founding.csv` |
| `pos_monthly`, `pos_dept` → `restmix` | Sana POS: loss and sales mix since open | `monthly.csv`, `dept.csv` |
| `hours_hourly` → `labour` | Sana staffing: hours, jobs and people | `hours_by_hour.json` (no names) |
| `ledger`, `costcalc`, `seasonal` | Sana: lean operations dashboard | ledger Apr–Sep 2026, Aug–Sep cost base |
