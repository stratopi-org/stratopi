# battery

## Install

```shell
pip install --user -r requirements.txt
```

Import PostgreSQL schema:

```shell
sudo su - postgres
psql -h 127.0.0.1 -d stratopi -U stratopi -f database-schema.sql --password
```

Install the service:

```shell
./install-service.sh
```

## Environment Variables

- POSTGRES_URL

## Utilities

- Create a PostgreSQL `pg_dump` backup of battery data:

```shell
python -m util.backup
```

## Pip

- `pip-outdated` to check if any requirements are outdated.
