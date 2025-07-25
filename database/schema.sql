CREATE TABLE t_country (
    c_id VARCHAR(32) PRIMARY KEY,
    c_name TEXT NOT NULL
);

CREATE TABLE t_province (
    p_id VARCHAR(32) PRIMARY KEY,
    p_name TEXT NOT NULL,
    c_id VARCHAR(32),
    FOREIGN KEY (c_id) REFERENCES t_country(c_id)
);

CREATE TABLE t_city (
    ci_id VARCHAR(32) PRIMARY KEY,
    ci_name TEXT NOT NULL,
    p_id VARCHAR(32),
    FOREIGN KEY (p_id) REFERENCES t_province(p_id)
);

CREATE TABLE t_postal_area (
    pa_id VARCHAR(32) PRIMARY KEY,
    pa_name TEXT,
    pa_code TEXT NOT NULL,
    pa_data JSONB,
    ci_id VARCHAR(32),
    FOREIGN KEY (ci_id) REFERENCES t_city(ci_id)
);