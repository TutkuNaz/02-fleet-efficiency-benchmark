# Executed SQL results

Generated from the 234-row EPA-derived sample.

## 1. Balanced source observations by model year

| year | source_observations | distinct_models | avg_city_mpg | avg_highway_mpg | avg_combined_mpg |
| --- | --- | --- | --- | --- | --- |
| 1999 | 117 | 38 | 17.02 | 23.43 | 19.38 |
| 2008 | 117 | 38 | 16.7 | 23.45 | 19.17 |

## 2. Vehicle-class efficiency and consumption benchmark

| class | observations | avg_combined_mpg | avg_gal_per_100mi | efficiency_rank |
| --- | --- | --- | --- | --- |
| subcompact | 35 | 23.24 | 4.47 | 1 |
| compact | 47 | 23.11 | 4.41 | 2 |
| midsize | 41 | 21.81 | 4.62 | 3 |
| 2seater | 5 | 18.56 | 5.39 | 4 |
| minivan | 11 | 18.21 | 5.56 | 5 |
| suv | 62 | 15.23 | 6.74 | 6 |
| pickup | 33 | 14.49 | 7.06 | 7 |

## 3. Manufacturer benchmark using distinct models rather than configuration rows

| manufacturer | distinct_models | model_year_observations | avg_combined_mpg | avg_displacement | efficiency_rank |
| --- | --- | --- | --- | --- | --- |
| volkswagen | 4 | 8 | 23.81 | 2.26 | 1 |
| toyota | 6 | 12 | 20.41 | 3.22 | 2 |
| audi | 3 | 6 | 20.35 | 2.66 | 3 |
| nissan | 3 | 6 | 20 | 3.33 | 4 |
| chevrolet | 4 | 8 | 17.24 | 5.08 | 5 |
| ford | 4 | 8 | 15.46 | 4.66 | 6 |
| dodge | 4 | 8 | 14.67 | 4.49 | 7 |

## 4. Engine-size segmentation and fuel intensity

| displacement_segment | observations | avg_highway_mpg | avg_gal_per_100mi |
| --- | --- | --- | --- |
| <2.0L | 22 | 33.18 | 3.73 |
| 2.0-2.9L | 78 | 26.81 | 4.59 |
| 3.0L+ | 134 | 19.88 | 6.36 |
