# location

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
