import os
import subprocess
from lib import log


psql_cmd = f"psql -d {os.environ['POSTGRES_URL']} -c 'TRUNCATE TABLE environmental;'"
log.info('starting table truncation...')
subprocess.run(psql_cmd, shell=True)

log.info("successfully truncated table 'environmental'")
