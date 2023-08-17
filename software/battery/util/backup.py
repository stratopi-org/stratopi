import datetime
import tempfile
import os
import subprocess
from lib import log

PG_DUMP_FORMAT = 'custom'

now = datetime.datetime.now()
current_date = now.strftime("%Y_%m_%d")
backup_file = os.path.join(tempfile.gettempdir(), f'pricesd_pgsql_{current_date}.bin')

pg_dump_cmd = f"pg_dump --dbname={os.environ['POSTGRES_URL']} --format={PG_DUMP_FORMAT} --file={backup_file}"
subprocess.run(pg_dump_cmd, shell=True)

log.info(f"successfully created backup '{backup_file}'")
