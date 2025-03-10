# location

## Create PostgreSQL schema

```shell
sudo -u postgres psql -h 127.0.0.1 -d stratopi -U stratopi -f ./database-schema.sql --password
```

## Install systemd Service

```shell
./install.sh
```

## Environment Variables

- `LOG_LEVEL` _(default=INFO)_
- `POSTGRES_URL` _(required)_

## View Logs

```shell
./view-logs.sh [--follow]
```

## Utilities

- Create a PostgreSQL `pg_dump` backup of location data:

```shell
python -m util.backup
```

- Truncate all location data from PostgreSQL:

```shell
python -m util.truncate
```

- Export location data to a [KML](https://en.wikipedia.org/wiki/Keyhole_Markup_Language) file:

```shell
python -m util.export_to_kml
```

## Pip

- `pip-outdated` checks if any PyPI packages are outdated.
