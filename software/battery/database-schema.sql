CREATE EXTENSION IF NOT EXISTS citext;
CREATE SCHEMA IF NOT EXISTS stratopi;

CREATE TABLE stratopi.battery (
  id uuid DEFAULT gen_random_uuid(),
  percent NUMERIC(4, 1) NOT NULL,
  temperature NUMERIC(4, 1) NOT NULL,
  added TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  PRIMARY KEY (id)
);

CREATE INDEX added_idx
    ON stratopi.battery (added ASC);
