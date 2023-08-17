# battery

## Docker Compose

```shell
docker-compose build
docker-compose up
```

## Usage

```shell
usage: battery [-h] [--version]

options:
  -h, --help  show this help message and exit
  --version   show version and exit
```

## Environment Variables

- POSTGRES_URL

## Utilities

- Create a PostgreSQL `pg_dump` backup:

```shell
python -m utils.backup
```

## Pip

- `pip-outdated` to check if any requirements are outdated.
