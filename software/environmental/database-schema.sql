CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE environmental (
    id UUID DEFAULT gen_random_uuid(),

    -- BME280 (internal)
    in_temperature_c NUMERIC(4, 1) NOT NULL,
    in_pressure_hpa NUMERIC(5, 1) NOT NULL,
    in_humidity_rh NUMERIC(4, 1) NOT NULL,

    -- MS8607 (external)
    ex_temperature_c NUMERIC(4, 1) NOT NULL,
    ex_pressure_hpa NUMERIC(6, 2) NOT NULL,
    ex_humidity_rh NUMERIC(4, 1) NOT NULL,

    cpu_temperature_c NUMERIC(4, 1) NOT NULL,
    added TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id)
);

CREATE INDEX environmental_in_temperature_c_idx
    ON environmental (in_temperature_c DESC);

CREATE INDEX environmental_in_pressure_hpa_idx
    ON environmental (in_pressure_hpa DESC);

CREATE INDEX environmental_in_humidity_rh_idx
    ON environmental (in_humidity_rh DESC);

CREATE INDEX environmental_ex_temperature_c_idx
    ON environmental (ex_temperature_c DESC);

CREATE INDEX environmental_ex_pressure_hpa_idx
    ON environmental (ex_pressure_hpa DESC);

CREATE INDEX environmental_ex_humidity_rh_idx
    ON environmental (ex_humidity_rh DESC);

CREATE INDEX environmental_cpu_temperature_c_idx
    ON environmental (cpu_temperature_c DESC);

CREATE INDEX environmental_added_idx
    ON environmental (added ASC);

-- Attach trigger and call notify_insert() after insert
CREATE TRIGGER environmental_insert_notify
AFTER INSERT ON environmental
FOR EACH ROW
EXECUTE FUNCTION notify_insert();
