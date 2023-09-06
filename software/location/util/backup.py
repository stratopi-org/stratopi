import datetime
import tempfile
import os
import subprocess
from lib import log

PG_DUMP_FORMAT = 'custom'

now = datetime.datetime.now()
current_date = now.strftime("%Y_%m_%d_%H_%M_%S")
backup_file = os.path.join(tempfile.gettempdir(), f'stratopi_location_{current_date}_pgsql.bin')

pg_dump_cmd = f"pg_dump --dbname={os.environ['POSTGRES_URL']} -t location --format={PG_DUMP_FORMAT} --file={backup_file}"
log.info('starting pg_dump backup...')
subprocess.run(pg_dump_cmd, shell=True)

log.info(f"successfully created pg_dump backup '{backup_file}'")
