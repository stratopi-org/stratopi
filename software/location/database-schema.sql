CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE location (
    id uuid DEFAULT gen_random_uuid(),
    coordinates point,
    added TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id)
);

CREATE INDEX coordinates_idx
    ON location USING GIST(coordinates);

CREATE INDEX added_idx
    ON location (added ASC);
