import pandas as pd
from fleet_efficiency.pipeline import clean_data


def test_clean_data_creates_efficiency_features():
    frame = pd.DataFrame({
        "manufacturer": ["audi"], "model": ["a4"], "displ": [2.0], "year": [2008],
        "cyl": [4], "trans": ["manual(m6)"], "drv": ["f"], "cty": [20], "hwy": [30],
        "fl": ["p"], "class": ["compact"],
    })
    clean, quality = clean_data(frame)
    assert quality.rows_clean == 1
    assert clean.loc[0, "combined_mpg_proxy"] == 24.5
    assert round(clean.loc[0, "fuel_intensity_gal_per_100mi"], 4) == round(100 / 24.5, 4)
