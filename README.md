# Fleet Efficiency Benchmark

A historical vehicle-efficiency benchmark using an EPA-derived sample of popular 1999 and 2008 models.

## Objective

The project compares vehicle classes, engine displacement and model-year groups from a fleet-efficiency perspective. The goal is to identify meaningful operating-efficiency trade-offs without overstating what a small historical sample can support.

Questions addressed:

- Which vehicle classes are most efficient in the sample?
- How does engine displacement relate to highway fuel economy?
- Is there a measurable difference between the selected 1999 and 2008 groups?
- Which manufacturers rank highest after applying minimum sample thresholds?
- How does fuel intensity change across displacement segments?

## Data

Source: `plotnine.data.mpg` — **234 rows and 11 variables**, documented as an EPA-derived subset covering 38 popular models from 1999 and 2008.

- Documentation: https://plotnine.org/reference/mpg.html
- Original provenance: U.S. EPA / fueleconomy.gov
- EPA open-data license: https://edg.epa.gov/EPA_Data_License.html
- Raw input is generated locally with `python scripts/download_data.py`.

See [`data/README.md`](data/README.md) for provenance details.

## Approach

1. Standardize fields and remove exact duplicates.
2. Apply basic data-quality checks.
3. Calculate a weighted analytical MPG proxy: `0.55 × city MPG + 0.45 × highway MPG`.
4. Convert the proxy to gallons per 100 miles for an operating-cost-oriented view.
5. Materialize the analytical dataset in SQLite.
6. Use SQL for class, manufacturer and displacement benchmarking.
7. Compare model-year distributions with a Mann–Whitney U test.

The weighted MPG measure is an analytical proxy created for this project; it is not an official EPA combined MPG rating.

## Stack

Python · pandas · NumPy · SciPy · SQLite · SQL · Matplotlib · pytest · GitHub Actions

## Data Quality

The source contains **234 rows**. After removing **9 exact duplicates**, the analytical dataset contains **225 rows** with no source null cells.

## Analysis

![Fuel economy by year](reports/figures/fuel_economy_by_year.svg)

![Efficiency by class](reports/figures/efficiency_by_class.svg)

![Displacement vs highway MPG](reports/figures/displacement_vs_highway_mpg.svg)

Key findings:

- Median city/highway MPG is **17 / 25** in both model-year groups.
- Median weighted efficiency proxy: **20.50 MPG** for 1999 and **20.15 MPG** for 2008.
- Mann–Whitney U test: **p = 0.503**, providing no statistically clear evidence of a distribution shift in this sample.
- Compact vehicles have the highest median proxy at **23.15 MPG**; pickups have the lowest at **14.80 MPG**.
- Average fuel intensity rises from roughly **3.63 gal/100 mi** below 2.0L displacement to **6.19 gal/100 mi** at 3.0L and above.

## SQL

The SQL analysis includes CTEs, `CASE WHEN`, aggregation, sample-size filters and window-function ranking.

![Manufacturer benchmark](reports/figures/manufacturer_efficiency.svg)

Executed results are available in [`reports/sql_results.md`](reports/sql_results.md).

## Statistical Interpretation

The main conclusion is not that one model year is categorically better than the other. Within this selected sample, model year alone does not clearly separate efficiency distributions. Vehicle class and engine displacement provide more useful segmentation for the fleet-oriented question.

No machine-learning model is included because the dataset and business question are better suited to comparative and statistical analysis.

## Business Interpretation

- Compare vehicles within similar duty and class requirements before using MPG as a procurement criterion.
- Gallons per 100 miles can communicate operating-cost impact more directly than MPG alone.
- Results from this historical 1999/2008 sample should not be extrapolated to a current fleet.
- A production total-cost-of-ownership model would require acquisition cost, annual mileage, current fuel prices, maintenance and depreciation.

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/download_data.py
python scripts/run_analysis.py --input data/raw/mpg.csv
pytest -q
```

## Repository Layout

```text
02-fleet-efficiency-benchmark/
├── data/
├── notebooks/
├── scripts/
├── src/fleet_efficiency/
├── sql/
├── reports/
├── tests/
└── .github/workflows/ci.yml
```

## Limitations

- The dataset contains selected popular models from only 1999 and 2008.
- Rows represent vehicle configurations, not fleet utilization records.
- The weighted MPG metric is project-specific.
- EPA test-cycle ratings do not equal real-world fleet fuel consumption.
- Findings are descriptive and should not be interpreted causally.

## License

EPA-produced data are generally public domain unless otherwise specified. plotnine is MIT licensed and documents the dataset as EPA-derived. Repository code and original analysis are MIT licensed.
