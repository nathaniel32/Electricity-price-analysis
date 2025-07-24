select pa_code, pa_name, ci_name, p_name from t_postal_area
join t_city on t_city.ci_id = t_postal_area.ci_id
join t_province on t_province.p_id = t_city.p_id