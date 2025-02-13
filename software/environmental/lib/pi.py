import subprocess


def get_cpu_temperature():
    output = subprocess.check_output(["vcgencmd", "measure_temp"], encoding="utf-8")
    return float(output.strip().split("=")[1].split("'C")[0])
