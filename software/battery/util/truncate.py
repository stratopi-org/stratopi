import os
import subprocess
from lib import log


psql_cmd = f"psql -d {os.environ['POSTGRES_URL']} -c 'TRUNCATE TABLE battery;'"
subprocess.run(psql_cmd, shell=True)

log.info(f"successfully truncated table 'battery'")
