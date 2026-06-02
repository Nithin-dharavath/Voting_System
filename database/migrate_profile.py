import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.connection import get_db_cursor

def migrate():
    try:
        with get_db_cursor() as cursor:
            cursor.execute('ALTER TABLE users ADD COLUMN profile_picture VARCHAR(255) DEFAULT NULL')
            print("Column 'profile_picture' added successfully to 'users' table.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
