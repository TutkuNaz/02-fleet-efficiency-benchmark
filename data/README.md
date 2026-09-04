# Data provenance

**Dataset used for analysis:** `plotnine.data.mpg`, a 234-row teaching subset documented as fuel-economy data for 38 popular vehicle models in model years 1999 and 2008.

- Documentation: https://plotnine.org/reference/mpg.html
- Original provenance: U.S. EPA / fueleconomy.gov.
- EPA standard open-data license: https://edg.epa.gov/EPA_Data_License.html
- EPA states that, unless otherwise specified, data produced by the agency are public domain under 17 U.S.C. § 105.
- plotnine package license: MIT.
- Retrieval workflow: `python scripts/download_data.py` materializes the dataset from the installed plotnine package.
- Raw input is git-ignored; the reproducible script and derived analytical outputs are versioned instead.

This is a **historical benchmark**, not a current fleet market dataset. Results compare the selected 1999 and 2008 popular-model sample and should not be generalized to the full U.S. vehicle fleet.
