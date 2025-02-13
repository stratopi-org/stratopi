CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE environmental (
    id UUID DEFAULT gen_random_uuid(),
    temperature_c NUMERIC(4, 1) NOT NULL,
    pressure_hpa NUMERIC(5, 1) NOT NULL,
    humidity_rh NUMERIC(4, 1) NOT NULL,
    cpu_temperature_c NUMERIC(4, 1) NOT NULL,
    added TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id)
);

CREATE INDEX environmental_temperature_c_idx
    ON environmental (temperature_c DESC);

CREATE INDEX environmental_pressure_hpa_idx
    ON environmental (pressure_hpa DESC);

CREATE INDEX environmental_humidity_rh_idx
    ON environmental (humidity_rh DESC);

CREATE INDEX environmental_cpu_temperature_c_idx
    ON environmental (cpu_temperature_c DESC);

CREATE INDEX environmental_added_idx
    ON environmental (added ASC);
