from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu


@dataclass(frozen=True)
class DataQuality:
    rows_raw: int
    rows_clean: int
    duplicates_removed: int
    null_cells_raw: int


def load_data(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, DataQuality]:
    raw = df.copy()
    data = df.copy()
    for col in ["manufacturer", "model", "trans", "drv", "fl", "class"]:
        data[col] = data[col].astype("string").str.strip()
    for col in ["displ", "year", "cyl", "cty", "hwy"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    before = len(data)
    data = data.drop_duplicates().copy()
    duplicates_removed = before - len(data)
    valid = (
        data["year"].between(1980, 2030)
        & data["displ"].between(0.5, 10)
        & data["cyl"].between(2, 16)
        & data["cty"].between(5, 100)
        & data["hwy"].between(5, 100)
    )
    data = data.loc[valid].copy()
    # A transparent procurement proxy, not an EPA combined rating.
    data["combined_mpg_proxy"] = 0.55 * data["cty"] + 0.45 * data["hwy"]
    data["fuel_intensity_gal_per_100mi"] = 100 / data["combined_mpg_proxy"]
    data["efficiency_band"] = pd.cut(
        data["combined_mpg_proxy"],
        bins=[0, 18, 23, 28, np.inf],
        labels=["Low", "Moderate", "Efficient", "High"],
        include_lowest=True,
    )
    data = data.reset_index(drop=True)
    quality = DataQuality(
        rows_raw=len(raw),
        rows_clean=len(data),
        duplicates_removed=duplicates_removed,
        null_cells_raw=int(raw.isna().sum().sum()),
    )
    return data, quality


def write_sqlite(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        df.to_sql("vehicles", con, if_exists="replace", index=False)
        con.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_year ON vehicles(year)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_class ON vehicles(class)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_mfr ON vehicles(manufacturer)")


def _top_manufacturer_table(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("manufacturer", observed=True)
        .agg(
            observations=("model", "size"),
            median_city_mpg=("cty", "median"),
            median_highway_mpg=("hwy", "median"),
            median_combined_proxy=("combined_mpg_proxy", "median"),
        )
        .query("observations >= 5")
        .sort_values("median_combined_proxy", ascending=False)
    )


def summarize(df: pd.DataFrame, quality: DataQuality) -> dict:
    by_year = df.groupby("year", observed=True).agg(
        observations=("model", "size"),
        median_city_mpg=("cty", "median"),
        median_highway_mpg=("hwy", "median"),
        median_combined_proxy=("combined_mpg_proxy", "median"),
        median_fuel_intensity=("fuel_intensity_gal_per_100mi", "median"),
    )
    older = df.loc[df["year"] == df["year"].min(), "combined_mpg_proxy"]
    newer = df.loc[df["year"] == df["year"].max(), "combined_mpg_proxy"]
    stat, pvalue = mannwhitneyu(newer, older, alternative="two-sided")

    class_stats = (
        df.groupby("class", observed=True)
        .agg(observations=("model", "size"), median_combined_proxy=("combined_mpg_proxy", "median"))
        .sort_values("median_combined_proxy", ascending=False)
    )
    manufacturers = _top_manufacturer_table(df)
    return {
        "data_quality": asdict(quality),
        "years": [int(df["year"].min()), int(df["year"].max())],
        "manufacturer_count": int(df["manufacturer"].nunique()),
        "model_count": int(df["model"].nunique()),
        "median_highway_mpg": float(df["hwy"].median()),
        "median_city_mpg": float(df["cty"].median()),
        "median_combined_proxy": float(df["combined_mpg_proxy"].median()),
        "year_comparison": {str(int(idx)): row.to_dict() for idx, row in by_year.iterrows()},
        "mann_whitney_u": float(stat),
        "mann_whitney_pvalue": float(pvalue),
        "most_efficient_class": str(class_stats.index[0]),
        "most_efficient_class_median_proxy": float(class_stats.iloc[0]["median_combined_proxy"]),
        "least_efficient_class": str(class_stats.index[-1]),
        "least_efficient_class_median_proxy": float(class_stats.iloc[-1]["median_combined_proxy"]),
        "top_manufacturer_by_proxy": str(manufacturers.index[0]),
        "top_manufacturer_median_proxy": float(manufacturers.iloc[0]["median_combined_proxy"]),
    }


def save_figures(df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    year = df.groupby("year", observed=True).agg(city=("cty", "median"), highway=("hwy", "median"))
    fig, ax = plt.subplots(figsize=(8, 4.8))
    x = np.arange(len(year.index)); width = 0.34
    ax.bar(x - width / 2, year["city"], width, label="City")
    ax.bar(x + width / 2, year["highway"], width, label="Highway")
    ax.set_xticks(x, [str(int(y)) for y in year.index])
    ax.set(title="Median fuel economy by model year", xlabel="Model year", ylabel="Miles per gallon")
    ax.legend(); fig.tight_layout(); fig.savefig(output_dir / "fuel_economy_by_year.png", dpi=180); plt.close(fig)

    cls = df.groupby("class", observed=True)["combined_mpg_proxy"].median().sort_values()
    fig, ax = plt.subplots(figsize=(8, 5.2)); cls.plot(kind="barh", ax=ax)
    ax.set(title="Efficiency proxy by vehicle class", xlabel="Median weighted MPG proxy", ylabel="Vehicle class")
    fig.tight_layout(); fig.savefig(output_dir / "efficiency_by_class.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for year_value, group in df.groupby("year", observed=True):
        ax.scatter(group["displ"], group["hwy"], alpha=0.62, s=30, label=str(int(year_value)))
    ax.set(title="Highway MPG versus engine displacement", xlabel="Engine displacement (L)", ylabel="Highway MPG")
    ax.legend(title="Model year"); fig.tight_layout(); fig.savefig(output_dir / "displacement_vs_highway_mpg.png", dpi=180); plt.close(fig)

    drv = df.groupby("drv", observed=True)["combined_mpg_proxy"].median().sort_values()
    fig, ax = plt.subplots(figsize=(7, 4.5)); drv.plot(kind="barh", ax=ax)
    ax.set(title="Efficiency proxy by drivetrain", xlabel="Median weighted MPG proxy", ylabel="Drivetrain code")
    fig.tight_layout(); fig.savefig(output_dir / "efficiency_by_drivetrain.png", dpi=180); plt.close(fig)

    mfr = _top_manufacturer_table(df).sort_values("median_combined_proxy")
    fig, ax = plt.subplots(figsize=(8, 6)); ax.barh(mfr.index, mfr["median_combined_proxy"])
    ax.set(title="Manufacturer efficiency benchmark", xlabel="Median weighted MPG proxy", ylabel="Manufacturer")
    fig.tight_layout(); fig.savefig(output_dir / "manufacturer_efficiency.png", dpi=180); plt.close(fig)


def run(raw_path: Path, project_root: Path) -> dict:
    raw = load_data(raw_path)
    clean, quality = clean_data(raw)
    processed = project_root / "data" / "processed" / "fleet_efficiency_clean.csv"
    processed.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(processed, index=False)
    write_sqlite(clean, project_root / "data" / "processed" / "fleet_efficiency.sqlite")
    save_figures(clean, project_root / "reports" / "figures")
    summary = summarize(clean, quality)
    (project_root / "reports" / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
