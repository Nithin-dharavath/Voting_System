import time
from contextlib import contextmanager

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

from config import settings

POOL_NAME = "voting_system_pool"
_RETRY_DELAY = 1
_MAX_RETRIES = 1

_pool: MySQLConnectionPool | None = None


def get_pool() -> MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = MySQLConnectionPool(
            pool_name=POOL_NAME,
            pool_size=settings.db_pool_size,
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            pool_reset_session=True,
            connection_timeout=settings.db_pool_connection_timeout,
        )
    return _pool


def get_connection():
    return get_pool().get_connection()


@contextmanager
def get_db_cursor():
    last_exc = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                yield cursor
                conn.commit()
                return
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                conn.close()
        except mysql.connector.errors.OperationalError as e:
            last_exc = e
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)
                _pool is not None and _pool._remove_connections()
            else:
                raise last_exc
        except Exception as e:
            last_exc = e
            raise last_exc
