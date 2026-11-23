# Keeping the master in step with the source dashboards

The master artifact (slug `07c7a030-4299-4813-b99e-beac42939f97`) stores, in its `dash/sync`
document, which source artifact and asset each dataset was copied from.

| Master dataset | Source artifact slug | Source dataset |
|---|---|---|
| trybe_monthly | 6ff834a4-6b6a-45d8-84f0-4796798c29ec | monthly |
| founding | 6ff834a4-6b6a-45d8-84f0-4796798c29ec | founding |
| pos_monthly | cd9059e8-0a5d-4748-ac62-3abcc248f698 | monthly |
| pos_dept | cd9059e8-0a5d-4748-ac62-3abcc248f698 | dept |
| hours_hourly | 4e43cb55-31fc-4c45-b05f-1ed632c9bbac | hours_by_hour |
| ledger, costcalc, seasonal | 39790ac4-3bae-4a9d-815d-a15c22e825ff | ledger, costcalc, seasonal |
| salaries | (set by hand) | salaried lead per side from a given month: Adrienne on Sana, Jonah on the restaurant. Add a row with a new from_month when salaries change. |

## Sync steps (run daily by a scheduled task, or right after refreshing any source)

1. For each row above, read the source's `datasets/<source dataset>` document and take the
   blob id from `source.url` (`/_blob/<id>`).
2. If it differs from `dash/sync.sources.<dataset>.asset`, `copy_asset` it from the source
   into the master, then `update` the master's `datasets/<dataset>` with the new `source.url`
   and the source's `updated` value, and record the new id in `dash/sync`.
3. Nothing else changes: the page recomputes every figure from the copied files.
4. GitHub copy: if Trybe or POS changed, write the new small CSVs into `data/`
   (`trybe_monthly.csv`, `founding.csv`, `pos_monthly.csv`, `ledger.csv`, `costcalc.csv`,
   `seasonal.csv`), rebuild with `tools/build.py`, run `tools/smoke.py`, commit and push.
   `labour.csv` and `restmix.csv` are aggregates; refresh them in the same session that
   pulls new Push or POS data (sum Push clocked hours by month and department; POS Food
   total / Drinks total net by month).
