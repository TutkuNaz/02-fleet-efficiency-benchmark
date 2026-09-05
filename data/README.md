# Data provenance

The project uses plotnine.data.mpg, a 234-row teaching sample documented as fuel-economy data for 38 popular vehicle models in model years 1999 and 2008.

- Documentation: https://plotnine.org/reference/mpg.html
- Original provenance: U.S. EPA / fueleconomy.gov
- EPA open-data terms: https://edg.epa.gov/EPA_Data_License.html
- Retrieval command: python scripts/download_data.py
- Expected scope: 234 configuration observations, 117 per year, covering the same 38 models in both years

The retrieval script materializes the dataset from the installed plotnine package. Raw input is Git-ignored; source instructions and compact derived outputs are versioned.

## Observation policy

The source contains nine rows that are exact duplicates across the published columns. They are detected and reported but retained: rows represent source configuration observations, and deleting them creates an unintended 114-versus-111 model-year imbalance. Comparisons are performed after aggregation to one median observation per model and year, then paired across the 38 shared models.

This is a historical benchmark, not a current fleet-market dataset. Results should not be generalized to all vehicles or treated as real-world fleet consumption without duty-cycle evidence.
