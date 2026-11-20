"""Process-local, bounded connection pools shared by all dashboard reads."""

import atexit
import os
from threading import Lock

from psycopg_pool import ConnectionPool


_pools = {}
_pool_lock = Lock()


def reset_connection(connection):
    """Restore defaults in idle state, before a connection can be borrowed again."""
    connection.autocommit = False
    connection.read_only = True
    connection.isolation_level = None
    connection.deferrable = None


def get_pool(database_url):
    # Lazy creation avoids opening connections in a prefork server's master.
    key = (os.getpid(), database_url)
    with _pool_lock:
        pool = _pools.get(key)
        if pool is None:
            pool = ConnectionPool(
                conninfo=database_url,
                name='dashboard',
                min_size=1,
                max_size=2,
                num_workers=1,
                timeout=5,
                max_idle=60,
                kwargs={'connect_timeout': 5},
                configure=reset_connection,
                reset=reset_connection,
                check=ConnectionPool.check_connection,
                open=False,
            )
            pool.open()
            _pools[key] = pool
        return pool


def read_connection(database_url):
    # The pool context handles commit/rollback, then returns the connection.
    return get_pool(database_url).connection()


def close_pools():
    with _pool_lock:
        keys = [key for key in _pools if key[0] == os.getpid()]
        pools = [_pools.pop(key) for key in keys]
    for pool in pools:
        pool.close()


atexit.register(close_pools)
