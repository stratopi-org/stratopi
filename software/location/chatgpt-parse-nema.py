from datetime import datetime


def parse_coordinate(coord_str, hemisphere):
    degrees = float(coord_str[:2])
    minutes = float(coord_str[2:])
    coordinate = degrees + minutes / 60.0
    return -coordinate if hemisphere in ['S', 'W'] else coordinate


def parse_cgpsinfo(cgpsinfo_data):
    try:
        data_fields = cgpsinfo_data.split(',')

        if len(data_fields) == 9:
            latitude = parse_coordinate(data_fields[0], data_fields[1])
            longitude = parse_coordinate(data_fields[2], data_fields[3])
            date = data_fields[4]
            time_utc = datetime.strptime(data_fields[5], '%H%M%S.%f').time()
            altitude_meters = float(data_fields[6])
            altitude_feet = altitude_meters * 3.28084
            speed_ms = float(data_fields[7])
            speed_knots = speed_ms * 1.94384
            course = float(data_fields[8])

            return {
                "Latitude": latitude,
                "Longitude": longitude,
                "Date": date,
                "Time (UTC)": time_utc,
                "Altitude (m)": altitude_meters,
                "Altitude (ft)": altitude_feet,
                "Speed (m/s)": speed_ms,
                "Speed (knots)": speed_knots,
                "Course": course
            }
    except (ValueError, IndexError, TypeError) as err:
        print(err)
        pass

    return None


# Example CGPSINFO data
cgpsinfo_data = "3609.197646,N,08651.641985,W,300823,062508.0,150.1,0.0,28.0"

parsed_data = parse_cgpsinfo(cgpsinfo_data)
if parsed_data:
    for key, value in parsed_data.items():
        print(f"{key}: {value}")
else:
    print("Invalid CGPSINFO data.")
