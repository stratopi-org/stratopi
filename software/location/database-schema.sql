CREATE EXTENSION IF NOT EXISTS citext;

DO $$ BEGIN
    IF to_regtype('DIRECTION') IS NULL THEN
        CREATE TYPE DIRECTION AS ENUM ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW');
    END IF;
END $$;

CREATE TABLE location (
    id UUID DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    time TIME NOT NULL,
    coordinates POINT NOT NULL,
    altitude_m NUMERIC(6, 1) NOT NULL,
    vertical_speed_mpm NUMERIC(5, 1),
    speed_kn NUMERIC(4, 1) NOT NULL,
    course_d NUMERIC(4, 1) NOT NULL,
    direction DIRECTION NOT NULL,
    added TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id)
);

CREATE INDEX location_date_idx
    ON location (date ASC);

CREATE INDEX location_time_idx
    ON location (time ASC);

CREATE INDEX location_timestamp_idx
    ON location ((date + time));

CREATE INDEX location_coordinates_idx
    ON location USING GIST(coordinates);

CREATE INDEX location_altitude_m_idx
    ON location (altitude_m ASC);

CREATE INDEX location_speed_kn_idx
    ON location (speed_kn ASC);

CREATE INDEX location_added_idx
    ON location (added ASC);

-- Trigger that automatically calcualtes vertical speed based on altitude and time deltas
CREATE OR REPLACE FUNCTION calculate_vertical_speed()
RETURNS TRIGGER AS $$
DECLARE
    previous_altitude NUMERIC;
    previous_date DATE;
    previous_time TIME;
    elapsed_seconds NUMERIC;
BEGIN
    -- Get the most recent previous location.
    SELECT
        altitude_m,
        date,
        time
    INTO
        previous_altitude,
        previous_date,
        previous_time
    FROM location
    ORDER BY date DESC, time DESC
    LIMIT 1;

    -- No previous reading means vertical speed cannot be calculated.
    IF previous_altitude IS NULL THEN
        NEW.vertical_speed_mpm := NULL;
        RETURN NEW;
    END IF;

    -- Calculate actual elapsed time between GPS readings.
    elapsed_seconds :=
        EXTRACT(
            EPOCH FROM
            ((NEW.date + NEW.time) - (previous_date + previous_time))
        );

    -- Protect against duplicate or out-of-order timestamps.
    IF elapsed_seconds <= 0 THEN
        NEW.vertical_speed_mpm := NULL;
        RETURN NEW;
    END IF;

    -- Calculate vertical speed in meters per minute.
    NEW.vertical_speed_mpm :=
        ROUND(
            (
                (NEW.altitude_m - previous_altitude)
                / elapsed_seconds
                * 60
            )::NUMERIC,
            1
        );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger and call calculate_vertical_speed() before insert
CREATE TRIGGER location_vertical_speed_trigger
BEFORE INSERT ON location
FOR EACH ROW
EXECUTE FUNCTION calculate_vertical_speed();
