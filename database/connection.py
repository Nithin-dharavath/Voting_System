import os
from contextlib import contextmanager

from dotenv import load_dotenv
from mysql.connector.pooling import MySQLConnectionPool

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "voting_system")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD")
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
POOL_NAME = "voting_system_pool"

_pool: MySQLConnectionPool | None = None


def get_pool() -> MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = MySQLConnectionPool(
            pool_name=POOL_NAME,
            pool_size=POOL_SIZE,
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
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
