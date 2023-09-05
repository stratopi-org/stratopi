CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE battery (
    id UUID DEFAULT gen_random_uuid(),
    percent NUMERIC(4, 1) NOT NULL,
    temperature_c SMALLINT NOT NULL,
    added TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id)
);

CREATE INDEX battery_percent_idx
    ON battery (percent DESC);

CREATE INDEX battery_added_idx
    ON battery (added ASC);
