CREATE TABLE locations (
    id serial PRIMARY KEY,
    name text,
    coordinates point
);

INSERT INTO locations (name, coordinates)
VALUES ('Location 1', '(-34.0522, -118.2437)');

