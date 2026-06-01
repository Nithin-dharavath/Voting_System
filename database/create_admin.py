import sys
from werkzeug.security import generate_password_hash
from database.connection import get_db_cursor

def create_admin():
    print("\n--- Admin Account Setup ---")
    full_name = input("Enter Admin Full Name: ")
    email = input("Enter Admin Email: ")
    password = input("Enter Admin Password: ")
    department = input("Enter Department (e.g., Administration): ")
    academic_year = input("Enter Academic Year (e.g., 2025-26): ")

    if len(password) < 8:
        print("\nError: Password must be at least 8 characters long.")
        return

    hashed_password = generate_password_hash(password)

    try:
        with get_db_cursor() as cursor:
            # Check if admin already exists
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                print(f"\nError: User with email {email} already exists.")
                return

            # Insert admin user
            query = """
            INSERT INTO users (full_name, email, password_hash, department, academic_year, role)
            VALUES (%s, %s, %s, %s, %s, 'ADMIN')
            """
            cursor.execute(query, (full_name, email, hashed_password, department, academic_year))
            print(f"\nSuccess! Admin account created for {email}.")
            print("You can now log in at /admin/login\n")

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    create_admin()
