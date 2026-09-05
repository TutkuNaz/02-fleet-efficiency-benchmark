from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

CITY_WEIGHT = 0.55
HIGHWAY_WEIGHT = 0.45
MIN_MANUFACTURER_MODELS = 3
REQUIRED_COLUMNS = {
    "manufacturer",
    "model",
    "displ",
    "year",
    "cyl",
    "trans",
    "drv",
    "cty",
    "hwy",
    "fl",
    "class",
}


@dataclass(frozen=True)
class DataQuality:
    rows_raw: int
    rows_clean: int
    duplicate_rows_detected: int
    invalid_rows_removed: int
    null_cells_raw: int


def load_data(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, DataQuality]:
    missing = sorted(REQUIRED_COLUMNS.difference(df.columns))
    if missing:
        raise ValueError(f"Input data is missing required columns: {', '.join(missing)}")

    raw = df.copy()
    data = df.copy()
    for col in ["manufacturer", "model", "trans", "drv", "fl", "class"]:
        data[col] = data[col].astype("string").str.strip()
    for col in ["displ", "year", "cyl", "cty", "hwy"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    duplicate_rows_detected = int(data.duplicated().sum())
    valid = (
        data["year"].between(1980, 2030)
        & data["displ"].between(0.5, 10)
        & data["cyl"].between(2, 16)
        & data["cty"].between(5, 100)
        & data["hwy"].between(5, 100)
    )
    invalid_rows_removed = int((~valid).sum())
    data = data.loc[valid].copy()

    # EPA combined fuel economy is a harmonic, consumption-weighted calculation:
    # 1 / (55% / city MPG + 45% / highway MPG).
    consumption = CITY_WEIGHT / data["cty"] + HIGHWAY_WEIGHT / data["hwy"]
    data["combined_mpg"] = 1 / consumption
    data["fuel_intensity_gal_per_100mi"] = 100 * consumption
    data["efficiency_band"] = pd.cut(
        data["combined_mpg"],
        bins=[0, 18, 23, 28, np.inf],
        labels=["Low", "Moderate", "Efficient", "High"],
        include_lowest=True,
    )
    data = data.reset_index(drop=True)
    quality = DataQuality(
        rows_raw=len(raw),
        rows_clean=len(data),
        duplicate_rows_detected=duplicate_rows_detected,
        invalid_rows_removed=invalid_rows_removed,
        null_cells_raw=int(raw.isna().sum().sum()),
    )
    return data, quality


def model_year_table(df: pd.DataFrame) -> pd.DataFrame:
    """Reduce configuration rows to one robust observation per model and year."""
    return (
        df.groupby(["manufacturer", "model", "year"], observed=True, as_index=False)
        .agg(
            configurations=("model", "size"),
            median_city_mpg=("cty", "median"),
            median_highway_mpg=("hwy", "median"),
            median_combined_mpg=("combined_mpg", "median"),
            median_fuel_intensity=("fuel_intensity_gal_per_100mi", "median"),
        )
    )


def paired_model_year_comparison(
    df: pd.DataFrame,
    bootstrap_samples: int = 10_000,
    random_state: int = 42,
) -> dict:
    years = sorted(int(value) for value in df["year"].unique())
    if len(years) != 2:
        raise ValueError("Paired comparison requires exactly two model years")

    older_year, newer_year = years
    paired = (
        model_year_table(df)
        .pivot(
            index=["manufacturer", "model"],
            columns="year",
            values="median_combined_mpg",
        )
        .dropna(subset=[older_year, newer_year])
    )
    if paired.empty:
        raise ValueError("No models are represented in both comparison years")

    differences = (paired[newer_year] - paired[older_year]).to_numpy()
    statistic, pvalue = wilcoxon(
        paired[newer_year],
        paired[older_year],
        alternative="two-sided",
        method="approx",
    )
    rng = np.random.default_rng(random_state)
    resampled = rng.choice(
        differences,
        size=(bootstrap_samples, len(differences)),
        replace=True,
    )
    bootstrap_medians = np.median(resampled, axis=1)
    ci_low, ci_high = np.quantile(bootstrap_medians, [0.025, 0.975])

    return {
        "older_year": older_year,
        "newer_year": newer_year,
        "paired_models": int(len(paired)),
        "median_change_mpg": float(np.median(differences)),
        "bootstrap_95_ci_mpg": [float(ci_low), float(ci_high)],
        "models_improved": int((differences > 0).sum()),
        "models_unchanged": int((differences == 0).sum()),
        "models_declined": int((differences < 0).sum()),
        "wilcoxon_statistic": float(statistic),
        "wilcoxon_pvalue": float(pvalue),
    }


def write_sqlite(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        df.to_sql("vehicles", connection, if_exists="replace", index=False)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_year ON vehicles(year)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_class ON vehicles(class)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_mfr ON vehicles(manufacturer)")


def _format_markdown_value(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        value = round(value, 4)
        if value.is_integer():
            value = int(value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows returned._"
    columns = [str(column) for column in frame.columns]
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(_format_markdown_value(value) for value in row) + " |"
        for row in frame.itertuples(index=False, name=None)
    ]
    return "\n".join([header, divider, *rows])


def write_sql_report(database_path: Path, query_path: Path, output_path: Path) -> None:
    sections: list[str] = []
    script = query_path.read_text(encoding="utf-8")
    with sqlite3.connect(database_path) as connection:
        for index, block in enumerate(script.split(";"), start=1):
            statement = block.strip()
            if not statement:
                continue
            title = next(
                (
                    line.removeprefix("--").strip()
                    for line in statement.splitlines()
                    if line.strip().startswith("--")
                ),
                f"Query {index}",
            )
            result = pd.read_sql_query(statement, connection)
            sections.append(f"## {title}\n\n{_markdown_table(result)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "# Executed SQL results\n\n"
        "Generated by the reproducible pipeline from the cleaned SQLite dataset.\n\n"
        + "\n\n".join(sections)
        + "\n",
        encoding="utf-8",
    )


def top_manufacturer_table(df: pd.DataFrame) -> pd.DataFrame:
    return (
        model_year_table(df)
        .groupby("manufacturer", observed=True)
        .agg(
            distinct_models=("model", "nunique"),
            model_year_observations=("model", "size"),
            median_city_mpg=("median_city_mpg", "median"),
            median_highway_mpg=("median_highway_mpg", "median"),
            median_combined_mpg=("median_combined_mpg", "median"),
        )
        .loc[lambda frame: frame["distinct_models"] >= MIN_MANUFACTURER_MODELS]
        .sort_values("median_combined_mpg", ascending=False)
    )


def summarize(df: pd.DataFrame, quality: DataQuality) -> dict:
    per_model_year = model_year_table(df)
    by_year = per_model_year.groupby("year", observed=True).agg(
        models=("model", "size"),
        median_city_mpg=("median_city_mpg", "median"),
        median_highway_mpg=("median_highway_mpg", "median"),
        median_combined_mpg=("median_combined_mpg", "median"),
        median_fuel_intensity=("median_fuel_intensity", "median"),
    )
    class_stats = (
        df.groupby("class", observed=True)
        .agg(
            observations=("model", "size"),
            median_combined_mpg=("combined_mpg", "median"),
        )
        .sort_values("median_combined_mpg", ascending=False)
    )
    manufacturers = top_manufacturer_table(df)
    if manufacturers.empty:
        raise ValueError(
            f"No manufacturer has at least {MIN_MANUFACTURER_MODELS} distinct models"
        )

    return {
        "data_quality": asdict(quality),
        "years": [int(df["year"].min()), int(df["year"].max())],
        "source_observations_by_year": {
            str(int(year)): int(count)
            for year, count in df.groupby("year", observed=True).size().items()
        },
        "manufacturer_count": int(df["manufacturer"].nunique()),
        "model_count": int(df["model"].nunique()),
        "median_highway_mpg": float(df["hwy"].median()),
        "median_city_mpg": float(df["cty"].median()),
        "median_combined_mpg": float(df["combined_mpg"].median()),
        "year_comparison": {
            str(int(index)): row.to_dict() for index, row in by_year.iterrows()
        },
        "paired_comparison": paired_model_year_comparison(df),
        "most_efficient_class": str(class_stats.index[0]),
        "most_efficient_class_median_mpg": float(
            class_stats.iloc[0]["median_combined_mpg"]
        ),
        "least_efficient_class": str(class_stats.index[-1]),
        "least_efficient_class_median_mpg": float(
            class_stats.iloc[-1]["median_combined_mpg"]
        ),
        "manufacturer_minimum_distinct_models": MIN_MANUFACTURER_MODELS,
        "top_manufacturer": str(manufacturers.index[0]),
        "top_manufacturer_median_mpg": float(
            manufacturers.iloc[0]["median_combined_mpg"]
        ),
    }


def save_figures(df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    per_model_year = model_year_table(df)

    year = per_model_year.groupby("year", observed=True).agg(
        city=("median_city_mpg", "median"),
        highway=("median_highway_mpg", "median"),
    )
    fig, ax = plt.subplots(figsize=(8, 4.8))
    x = np.arange(len(year.index))
    width = 0.34
    ax.bar(x - width / 2, year["city"], width, label="City")
    ax.bar(x + width / 2, year["highway"], width, label="Highway")
    ax.set_xticks(x, [str(int(value)) for value in year.index])
    ax.set(title="Median fuel economy by model year", xlabel="Model year", ylabel="Miles per gallon")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "fuel_economy_by_year.svg", bbox_inches="tight")
    plt.close(fig)

    classes = df.groupby("class", observed=True)["combined_mpg"].median().sort_values()
    fig, ax = plt.subplots(figsize=(8, 5.2))
    classes.plot(kind="barh", ax=ax)
    ax.set(title="EPA combined MPG by vehicle class", xlabel="Median combined MPG", ylabel="Vehicle class")
    fig.tight_layout()
    fig.savefig(output_dir / "efficiency_by_class.svg", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for year_value, group in df.groupby("year", observed=True):
        ax.scatter(group["displ"], group["hwy"], alpha=0.62, s=30, label=str(int(year_value)))
    ax.set(title="Highway MPG versus engine displacement", xlabel="Engine displacement (L)", ylabel="Highway MPG")
    ax.legend(title="Model year")
    fig.tight_layout()
    fig.savefig(output_dir / "displacement_vs_highway_mpg.svg", bbox_inches="tight")
    plt.close(fig)

    drivetrain = df.groupby("drv", observed=True)["combined_mpg"].median().sort_values()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    drivetrain.plot(kind="barh", ax=ax)
    ax.set(title="EPA combined MPG by drivetrain", xlabel="Median combined MPG", ylabel="Drivetrain code")
    fig.tight_layout()
    fig.savefig(output_dir / "efficiency_by_drivetrain.svg", bbox_inches="tight")
    plt.close(fig)

    manufacturers = top_manufacturer_table(df).sort_values("median_combined_mpg")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(manufacturers.index, manufacturers["median_combined_mpg"])
    ax.set(
        title=f"Manufacturer benchmark (at least {MIN_MANUFACTURER_MODELS} distinct models)",
        xlabel="Median model-year combined MPG",
        ylabel="Manufacturer",
    )
    fig.tight_layout()
    fig.savefig(output_dir / "manufacturer_efficiency.svg", bbox_inches="tight")
    plt.close(fig)


def run(raw_path: Path, project_root: Path) -> dict:
    raw = load_data(raw_path)
    clean, quality = clean_data(raw)

    processed_dir = project_root / "data" / "processed"
    reports_dir = project_root / "reports"
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    processed_csv = processed_dir / "fleet_efficiency_clean.csv"
    database_path = processed_dir / "fleet_efficiency.sqlite"
    clean.to_csv(processed_csv, index=False)
    write_sqlite(clean, database_path)
    write_sql_report(
        database_path,
        project_root / "sql" / "business_analysis.sql",
        reports_dir / "sql_results.md",
    )
    save_figures(clean, reports_dir / "figures")
    summary = summarize(clean, quality)
    (reports_dir / "metrics.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return summary
