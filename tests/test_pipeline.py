from pathlib import Path

import pandas as pd
import pytest

from fleet_efficiency.pipeline import clean_data, paired_model_year_comparison, run


def _row(**overrides):
    row = {
        "manufacturer": "audi",
        "model": "a4",
        "displ": 2.0,
        "year": 2008,
        "cyl": 4,
        "trans": "manual(m6)",
        "drv": "f",
        "cty": 20,
        "hwy": 30,
        "fl": "p",
        "class": "compact",
    }
    row.update(overrides)
    return row


def _paired_fixture() -> pd.DataFrame:
    records = []
    shifts = [-1, 1, 2]
    for model_index in range(9):
        manufacturer = f"maker-{model_index // 3}"
        model = f"model-{model_index}"
        for year in [1999, 2008]:
            shift = shifts[model_index % 3] if year == 2008 else 0
            for configuration in range(2):
                city = 15 + model_index + configuration + shift
                records.append(
                    _row(
                        manufacturer=manufacturer,
                        model=model,
                        displ=1.4 + model_index * 0.25,
                        year=year,
                        cty=city,
                        hwy=city + 8,
                        trans="auto(l5)" if configuration else "manual(m6)",
                        drv=["f", "r", "4"][model_index % 3],
                        **{"class": ["compact", "midsize", "suv"][model_index % 3]},
                    )
                )
    return pd.DataFrame.from_records(records)


def test_clean_data_uses_epa_harmonic_combined_mpg():
    clean, quality = clean_data(pd.DataFrame([_row()]))
    expected_mpg = 1 / (0.55 / 20 + 0.45 / 30)
    assert quality.rows_clean == 1
    assert clean.loc[0, "combined_mpg"] == pytest.approx(expected_mpg)
    assert clean.loc[0, "fuel_intensity_gal_per_100mi"] == pytest.approx(4.25)


def test_source_duplicate_rows_are_detected_and_retained():
    clean, quality = clean_data(pd.DataFrame([_row(), _row()]))
    assert len(clean) == 2
    assert quality.duplicate_rows_detected == 1


def test_paired_comparison_uses_one_observation_per_model_year():
    clean, _ = clean_data(_paired_fixture())
    comparison = paired_model_year_comparison(clean, bootstrap_samples=500)
    assert comparison["paired_models"] == 9
    assert comparison["models_improved"] == 6
    assert comparison["models_declined"] == 3
    assert comparison["median_change_mpg"] > 0


def test_run_materializes_every_output_from_a_fresh_directory(tmp_path: Path):
    raw_path = tmp_path / "mpg.csv"
    _paired_fixture().to_csv(raw_path, index=False)
    (tmp_path / "sql").mkdir()
    source_sql = Path(__file__).resolve().parents[1] / "sql" / "business_analysis.sql"
    (tmp_path / "sql" / "business_analysis.sql").write_text(
        source_sql.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    summary = run(raw_path, tmp_path)

    assert summary["paired_comparison"]["paired_models"] == 9
    assert (tmp_path / "data" / "processed" / "fleet_efficiency_clean.csv").is_file()
    assert (tmp_path / "data" / "processed" / "fleet_efficiency.sqlite").is_file()
    assert (tmp_path / "reports" / "sql_results.md").is_file()
    assert (tmp_path / "reports" / "metrics.json").is_file()
    assert len(list((tmp_path / "reports" / "figures").glob("*.svg"))) == 5
