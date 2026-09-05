# Fleet Efficiency Benchmark

[![CI](https://github.com/TutkuNaz/02-fleet-efficiency-benchmark/actions/workflows/ci.yml/badge.svg)](https://github.com/TutkuNaz/02-fleet-efficiency-benchmark/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A reproducible Python and SQL benchmark of historical EPA-derived vehicle fuel economy, with model-paired inference and fleet-oriented consumption metrics.

Part of the [Automotive Open Data Hub](https://github.com/TutkuNaz/automotive-data-portfolio), a curated collection of automotive datasets and reproducible starter analyses.

## What this project answers

- How did fuel economy change for the same 38 popular models between 1999 and 2008?
- Which vehicle classes and drivetrain groups differ most in fuel intensity?
- How does engine displacement relate to highway MPG?
- Which manufacturers rank highest when the threshold is based on distinct models rather than configuration count?

## Data

Source: [plotnine.data.mpg](https://plotnine.org/reference/mpg.html), a 234-row, 11-variable teaching sample derived from U.S. EPA / fueleconomy.gov data. It contains 117 configuration observations in each of 1999 and 2008 and covers the same 38 popular models in both years.

The pipeline detects nine exact duplicate source rows but retains the published observations. Blind deletion would create an unintended 114-versus-111 year imbalance. Statistical comparison instead aggregates configurations to one median observation per model-year and pairs the 38 shared models. See [data/README.md](data/README.md).

## Correct fuel-economy calculation

EPA combined MPG is calculated on a consumption basis, not as an arithmetic average:

    combined MPG = 1 / (0.55 / city MPG + 0.45 / highway MPG)
    gallons per 100 miles = 100 × (0.55 / city MPG + 0.45 / highway MPG)

The 55% city / 45% highway method follows the [EPA fuel-economy calculation](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P100B3EQ.TXT). Gallons per 100 miles makes operating consumption additive and easier to compare across vehicles.

## Analytical design

1. Validate the source schema and numeric ranges.
2. Preserve the balanced 234-row source while reporting duplicate observations.
3. Calculate EPA combined MPG and gallons per 100 miles.
4. Aggregate configurations to model-year medians.
5. Pair all models represented in both years.
6. Estimate the median paired change with a deterministic bootstrap interval.
7. Test the paired difference with a two-sided Wilcoxon signed-rank test.
8. Materialize the cleaned data in SQLite and execute version-controlled SQL.

## Findings

![Fuel economy by year](reports/figures/fuel_economy_by_year.svg)

![Efficiency by class](reports/figures/efficiency_by_class.svg)

![Displacement versus highway MPG](reports/figures/displacement_vs_highway_mpg.svg)

In this selected historical sample:

- the paired median change from 1999 to 2008 is approximately **+0.97 combined MPG**;
- **29 of 38** paired models improve and 9 decline;
- the deterministic 95% bootstrap interval for the median change is approximately **+0.30 to +1.37 MPG**;
- the paired Wilcoxon test gives **p < 0.001**;
- compact vehicles have the highest class median, while pickups have the lowest;
- larger-displacement groups consume materially more gallons per 100 miles.

These results describe a deliberately selected model sample. They do not imply that every 2008 vehicle is more efficient than every 1999 vehicle.

## Manufacturer benchmark

![Manufacturer benchmark](reports/figures/manufacturer_efficiency.svg)

The manufacturer table first creates model-year aggregates and then requires at least three distinct models. This prevents a manufacturer represented by many configurations of one model from being presented as a broad manufacturer benchmark.

The SQL layer covers balanced year counts, class efficiency, the distinct-model manufacturer threshold, and displacement-segment fuel intensity. The pipeline regenerates [reports/sql_results.md](reports/sql_results.md) directly from [sql/business_analysis.sql](sql/business_analysis.sql).

## Run locally

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    python scripts/download_data.py
    python scripts/run_analysis.py
    python -m pytest -q

Windows activation: .venv\Scripts\activate

The analysis writes a cleaned CSV, an indexed SQLite database, metrics JSON, an executed SQL report, and five SVG figures. Missing output directories are created automatically.

## Repository layout

    02-fleet-efficiency-benchmark/
    ├── data/                 # provenance and local data boundaries
    ├── notebooks/            # transparent exploratory views
    ├── scripts/              # retrieval and analysis entry points
    ├── src/fleet_efficiency/ # tested analytical pipeline
    ├── sql/                  # executable business queries
    ├── reports/              # compact reference outputs
    ├── tests/                # formula, pairing, and end-to-end tests
    └── .github/              # CI and dependency updates

## Limitations

- The dataset covers selected popular models from only 1999 and 2008.
- Rows represent tested configurations, not sales-weighted fleets or utilization records.
- EPA ratings do not equal real-world consumption for a specific route, load, climate, or driver.
- Manufacturer rankings remain descriptive and are not procurement recommendations.
- A total-cost-of-ownership model also needs acquisition cost, mileage, fuel price, maintenance, and depreciation.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for the evidence checklist. Report vulnerabilities privately using [SECURITY.md](SECURITY.md).

## License

Repository code and original analysis are MIT licensed. EPA-produced data are generally public domain unless otherwise specified; plotnine is MIT licensed. Consult each upstream source for its current terms.
