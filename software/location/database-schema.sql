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

CREATE INDEX location_coordinates_idx
    ON location USING GIST(coordinates);

CREATE INDEX location_altitude_m_idx
    ON location (altitude_m ASC);

CREATE INDEX location_speed_kn_idx
    ON location (speed_kn ASC);

CREATE INDEX location_added_idx
    ON location (added ASC);
