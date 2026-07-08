# NHESS Frozen-Table Reproduction Summary

Generated from `data/frozen_tables/` by `scripts/reproduce_summary_tables.py`.

## Key Checks

- Pohang pixel/Sentinel ROC-AUC: 0.6118.
- Yecheon pixel/Sentinel ROC-AUC: 0.4490.
- Yecheon pixel/NIDR-only ROC-AUC: 0.6077.
- Yecheon EMD/KFS aggregate ROC-AUC: 0.1480.

These values preserve the revised manuscript's protocol-dependence finding: the measured signal changes with label source and scale.

## Generated Files

- `protocol_skill_summary.csv`
- `terrain_contrast_summary.csv`
- `aggregate_reversal_summary.csv`
