import mysql.connector
import os
from dotenv import load_dotenv
from database.connection import get_db_cursor

load_dotenv()

try:
    with get_db_cursor() as cursor:
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        print("Users Table Structure:")
        for col in columns:
            print(col)
except Exception as e:
    print(f"Error: {e}")
