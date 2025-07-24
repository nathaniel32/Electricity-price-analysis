select pa_code, pa_name, ci_name, p_name from t_postal_area
join t_city on t_city.ci_id = t_postal_area.ci_id
join t_province on t_province.p_id = t_city.p_id

-- total duplicate
SELECT SUM(dupe_count - 1) AS total_duplicates
FROM (
    SELECT COUNT(*) AS dupe_count
    FROM t_postal_area
    GROUP BY pa_code
    HAVING COUNT(*) > 1
);

-- 19.529 - 11.274 = 8.255