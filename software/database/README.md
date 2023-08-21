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

Create the StratoPi PostgreSQL user.

```shell
sudo su - postgres
createuser --interactive --pwprompt
```

Create the StratoPi PostgreSQL database.

```shell
sudo su - postgres
createdb stratopi --owner=stratopi
```

Grant PostgreSQL privileges.

```shell
sudo su - postgres
psql -d stratopi
GRANT ALL PRIVILEGES ON DATABASE stratopi TO stratopi;
```

Adjust PostgreSQL host-based authentication. Append to file `/etc/postgresql/15/main/pg_hba.conf`:

```
local   stratopi        stratopi                                trust
host    stratopi        stratopi        127.0.0.1/32            trust
host    stratopi        stratopi        10.0.0.1/22             trust
```

```shell
sudo service postgresql restart
```
