CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE environmental (
    id UUID DEFAULT gen_random_uuid(),
    added TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id)
);

CREATE INDEX environmental_added_idx
    ON environmental (added ASC);
