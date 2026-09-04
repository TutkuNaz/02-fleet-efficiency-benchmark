-- 1. Model-year efficiency benchmark
WITH yearly AS (
    SELECT year,
           COUNT(*) AS observations,
           AVG(cty) AS avg_city_mpg,
           AVG(hwy) AS avg_highway_mpg,
           AVG(combined_mpg_proxy) AS avg_combined_proxy
    FROM vehicles
    GROUP BY year
)
SELECT * FROM yearly ORDER BY year;

-- 2. Rank vehicle classes by efficiency proxy.
WITH class_efficiency AS (
    SELECT class,
           COUNT(*) AS observations,
           AVG(combined_mpg_proxy) AS avg_efficiency_proxy,
           AVG(fuel_intensity_gal_per_100mi) AS avg_gal_per_100mi
    FROM vehicles
    GROUP BY class
)
SELECT class, observations, avg_efficiency_proxy, avg_gal_per_100mi,
       DENSE_RANK() OVER (ORDER BY avg_efficiency_proxy DESC) AS efficiency_rank
FROM class_efficiency
ORDER BY efficiency_rank, class;

-- 3. Procurement-style manufacturer benchmark with minimum sample size.
WITH manufacturer_stats AS (
    SELECT manufacturer,
           COUNT(*) AS observations,
           AVG(combined_mpg_proxy) AS avg_efficiency_proxy,
           AVG(displ) AS avg_displacement
    FROM vehicles
    GROUP BY manufacturer
    HAVING COUNT(*) >= 5
)
SELECT manufacturer, observations, avg_efficiency_proxy, avg_displacement,
       RANK() OVER (ORDER BY avg_efficiency_proxy DESC) AS efficiency_rank
FROM manufacturer_stats
ORDER BY efficiency_rank;

-- 4. Engine-size segmentation and fuel intensity.
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
