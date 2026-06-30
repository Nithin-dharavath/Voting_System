from database.connection import get_db_cursor


def setup_profile_icons():
    print("\n--- Setting up Profile Icons Table ---")
    try:
        with get_db_cursor() as cursor:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS profile_icons (
                user_id INT PRIMARY KEY,
                file_path VARCHAR(512) NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            """
            cursor.execute(create_table_query)
            print("Table 'profile_icons' created or already exists.")
    except Exception as e:
        print(f"An error occurred while creating the table: {e}")


if __name__ == "__main__":
    setup_profile_icons()
