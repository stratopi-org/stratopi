from datetime import datetime








# Example CGPSINFO data
cgpsinfo_data = "3609.197646,N,08651.641985,W,300823,062508.0,150.1,0.0,28.0"

parsed_data = parse_cgpsinfo(cgpsinfo_data)
if parsed_data:
    for key, value in parsed_data.items():
        print(f"{key}: {value}")
else:
    print("Invalid CGPSINFO data.")
