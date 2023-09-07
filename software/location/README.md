# location

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

- Truncate all PostgreSQL data from table `battery`:

```shell
python -m util.truncate
```

## Pip

- `pip-outdated` to check if any requirements are outdated.

# KML format

```xml
<Placemark>
    <name>Line with Date and Time</name>
    <TimeStamp>
        <when>2023-09-06T03:45:53Z</when>
    </TimeStamp>
    <LineString>
        <coordinates>
            -86.860732117,36.153173317,185.1
            -86.861234567,36.153567890,190.5
            <!-- Add more points with altitude as needed -->
        </coordinates>
    </LineString>
</Placemark>
```

or?


```xml
<Placemark>
    <name>Point 1</name>
    <TimeStamp>
        <when>2023-09-06T03:45:53Z</when>
    </TimeStamp>
    <Point>
        <coordinates>-86.860732117,36.153173317,185.1</coordinates>
    </Point>
</Placemark>
<Placemark>
    <name>Point 2</name>
    <TimeStamp>
        <when>2023-09-06T04:00:00Z</when>
    </TimeStamp>
    <Point>
        <coordinates>-86.861234567,36.153567890,190.5</coordinates>
    </Point>
</Placemark>
```
