# battery

## Install

```shell
pip install --user -r requirements.txt
```

## Usage

```shell
usage: python app.py [-h] [--version]

options:
  -h, --help  show this help message and exit
  --version   show version and exit
```

## Environment Variables

- POSTGRES_URL

## Utilities

- Create a PostgreSQL `pg_dump` backup:

```shell
python -m util.backup
```

## Pip

- `pip-outdated` to check if any requirements are outdated.
