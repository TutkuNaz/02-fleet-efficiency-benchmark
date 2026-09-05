-- 1. Balanced source observations by model year
SELECT year,
       COUNT(*) AS source_observations,
       COUNT(DISTINCT manufacturer || ':' || model) AS distinct_models,
       ROUND(AVG(cty), 2) AS avg_city_mpg,
       ROUND(AVG(hwy), 2) AS avg_highway_mpg,
       ROUND(AVG(combined_mpg), 2) AS avg_combined_mpg
FROM vehicles
GROUP BY year
ORDER BY year;

-- 2. Vehicle-class efficiency and consumption benchmark
SELECT class,
       COUNT(*) AS observations,
       ROUND(AVG(combined_mpg), 2) AS avg_combined_mpg,
       ROUND(AVG(fuel_intensity_gal_per_100mi), 2) AS avg_gal_per_100mi,
       DENSE_RANK() OVER (ORDER BY AVG(combined_mpg) DESC) AS efficiency_rank
FROM vehicles
GROUP BY class
ORDER BY efficiency_rank, class;

-- 3. Manufacturer benchmark using distinct models rather than configuration rows
WITH model_year AS (
    SELECT manufacturer,
           model,
           year,
           AVG(combined_mpg) AS model_year_combined_mpg,
           AVG(displ) AS model_year_displacement
    FROM vehicles
    GROUP BY manufacturer, model, year
), manufacturer_stats AS (
    SELECT manufacturer,
           COUNT(DISTINCT model) AS distinct_models,
           COUNT(*) AS model_year_observations,
           AVG(model_year_combined_mpg) AS avg_combined_mpg,
           AVG(model_year_displacement) AS avg_displacement
    FROM model_year
    GROUP BY manufacturer
    HAVING COUNT(DISTINCT model) >= 3
)
SELECT manufacturer,
       distinct_models,
       model_year_observations,
       ROUND(avg_combined_mpg, 2) AS avg_combined_mpg,
       ROUND(avg_displacement, 2) AS avg_displacement,
       RANK() OVER (ORDER BY avg_combined_mpg DESC) AS efficiency_rank
FROM manufacturer_stats
ORDER BY efficiency_rank;

-- 4. Engine-size segmentation and fuel intensity
SELECT CASE
           WHEN displ < 2.0 THEN '<2.0L'
           WHEN displ < 3.0 THEN '2.0-2.9L'
           ELSE '3.0L+'
       END AS displacement_segment,
       COUNT(*) AS observations,
       ROUND(AVG(hwy), 2) AS avg_highway_mpg,
       ROUND(AVG(fuel_intensity_gal_per_100mi), 2) AS avg_gal_per_100mi
FROM vehicles
GROUP BY displacement_segment
ORDER BY avg_gal_per_100mi;
