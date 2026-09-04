"""Materialize the EPA-derived mpg dataset distributed with plotnine.

plotnine documents this 234-row teaching dataset as fuel-economy data for 38
popular models in 1999 and 2008; original provenance is fueleconomy.gov / EPA.
"""
from pathlib import Path
from plotnine.data import mpg

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "data" / "raw" / "mpg.csv"
out.parent.mkdir(parents=True, exist_ok=True)
mpg.to_csv(out, index=False)
print(f"Wrote {len(mpg):,} rows to {out}")
