# battery

## Create PostgreSQL schema:

```shell
sudo -u postgres psql -h 127.0.0.1 -d stratopi -U stratopi -f ./database-schema.sql --password
```

## Install

```shell
./install.sh
```

## Environment Variables

- POSTGRES_URL

## Utilities

- Create a PostgreSQL `pg_dump` backup of battery data:

```shell
python -m util.backup
```

- Truncate all battery data from PostgreSQL:

```shell
python -m util.truncate
```

## Pip

- `pip-outdated` to check if any requirements are outdated.
