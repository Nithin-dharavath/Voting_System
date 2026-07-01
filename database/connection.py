from contextlib import contextmanager

from mysql.connector.pooling import MySQLConnectionPool

from config import settings

POOL_NAME = "voting_system_pool"

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
        )
    return _pool


def get_connection():
    return get_pool().get_connection()


@contextmanager
def get_db_cursor():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
