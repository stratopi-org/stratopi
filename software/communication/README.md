# communication

## Create PostgreSQL Schema

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
- `SLACK_BOT_TOKEN` _(required)_
- `SLACK_CHANNEL_ID` _(required)_

## View Logs

```shell
./view-logs.sh [--follow]
```

## Pip

- `pip-outdated` checks if any PyPI packages are outdated.

