# database

- PostgreSQL 15

## Install

```shell
sudo apt-get install -y --no-install-recommends gcc lsb-release gnupg2
```

```shel
echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
curl -sSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update
sudo apt-get install -y --no-install-recommends libc-dev libpq-dev postgresql-15 postgresql-client-15
sudo apt-get -y autoremove
sudo apt-get clean
```

## Setup

Create the StratoPi database.

```shell
sudo su - postgres
createdb stratopi
```

Create the StratoPi PostgreSQL user.

```shell
sudo su - postgres
psql
CREATE USER stratopi WITH PASSWORD '<password-here>';
GRANT ALL PRIVILEGES ON SCHEMA stratopi TO stratopi;
```
