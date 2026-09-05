# Contributing

Contributions that improve source provenance, statistical design, reproducibility, tests, or fleet interpretation are welcome.

## Development workflow

1. Fork the repository and create a focused branch.
2. Use Python 3.11 or 3.12 in a virtual environment.
3. Install dependencies with pip install -r requirements.txt.
4. Run python scripts/download_data.py to materialize the packaged EPA-derived sample.
5. Run python scripts/run_analysis.py and python -m pytest -q.
6. Compile sources with python -m compileall -q src scripts.

## Evidence checklist

- Preserve the distinction between configuration rows, model-year aggregates, and paired models.
- Document formulas, thresholds, source licenses, and analytical assumptions.
- Add tests for calculation or statistical changes.
- Keep raw source data out of Git; commit only compact, reproducible reference outputs.
- Do not include credentials, personal information, or proprietary fleet data.

Open an issue before a substantial scope change or the addition of a new data source.
