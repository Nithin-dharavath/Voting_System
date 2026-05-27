import datetime
from werkzeug.security import generate_password_hash
from database.connection import get_db_cursor

def table_exists(cursor, table_name):
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    return len(cursor.fetchall()) > 0

def seed_database():
    print("\n--- Database Seeding Started ---")


    # Define seed data
    admin_user = {
        "full_name": "System Administrator",
        "email": "admin@college.edu",
        "password": "adminpassword123",
        "department": "Administration",
        "academic_year": "2025-26",
        "role": "ADMIN"
    }

    student_users = [
        {
            "full_name": "Alice Student",
            "email": "alice@college.edu",
            "password": "studentpassword123",
            "department": "Computer Science",
            "academic_year": "2025-26",
            "role": "STUDENT"
        },
        {
            "full_name": "Bob Student",
            "email": "bob@college.edu",
            "password": "studentpassword123",
            "department": "Electrical Engineering",
            "academic_year": "2025-26",
            "role": "STUDENT"
        }
    ]

    now = datetime.datetime.now()

    elections = [
        {
            "title": "General Secretary Election 2026",
            "description": "Election for the General Secretary position.",
            "start_time": now + datetime.timedelta(days=7),
            "end_time": now + datetime.timedelta(days=8),
            "result_published": 0
        },
        {
            "title": "Student Council President 2026",
            "description": "Election for the Student Council President.",
            "start_time": now - datetime.timedelta(days=1),
            "end_time": now + datetime.timedelta(days=1),
            "result_published": 0
        },
        {
            "title": "Cultural Fest Lead 2025",
            "description": "Election for the Cultural Fest Lead.",
            "start_time": now - datetime.timedelta(days=60),
            "end_time": now - datetime.timedelta(days=59),
            "result_published": 1
        }
    ]

    try:
        with get_db_cursor() as cursor:
            # 1. Clear existing election-related data
            print("Clearing existing election-related data...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

            tables_to_clear = [
                "vote_verifications",
                "votes",
                "voting_sessions",
                "candidate_applications",
                "elections"
            ]

            for table in tables_to_clear:
                if table_exists(cursor, table):
                    cursor.execute(f"TRUNCATE TABLE {table}")
                else:
                    print(f"Skipping TRUNCATE: Table {table} does not exist.")

            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")


            # 2. Insert Admin User
            if table_exists(cursor, "users"):
                print(f"Ensuring admin user exists: {admin_user['email']}...")
                cursor.execute("SELECT id FROM users WHERE email = %s", (admin_user['email'],))
                if not cursor.fetchone():
                    hashed_pw = generate_password_hash(admin_user['password'])
                    query = "INSERT INTO users (full_name, email, password_hash, department, academic_year, role) VALUES (%s, %s, %s, %s, %s, %s)"
                    cursor.execute(query, (
                        admin_user['full_name'],
                        admin_user['email'],
                        hashed_pw,
                        admin_user['department'],
                        admin_user['academic_year'],
                        admin_user['role']
                    ))
                    admin_id = cursor.lastrowid
                else:
                    cursor.execute("SELECT id FROM users WHERE email = %s", (admin_user['email'],))
                    admin_id = cursor.fetchone()['id']
            else:
                print("Skipping User insertion: Table 'users' does not exist.")
                admin_id = None


            # 3. Insert Student Users
            if table_exists(cursor, "users"):
                for student in student_users:
                    print(f"Ensuring student user exists: {student['email']}...")
                    cursor.execute("SELECT id FROM users WHERE email = %s", (student['email'],))
                    if not cursor.fetchone():
                        hashed_pw = generate_password_hash(student['password'])
                        query = "INSERT INTO users (full_name, email, password_hash, department, academic_year, role) VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(query, (
                            student['full_name'],
                            student['email'],
                            hashed_pw,
                            student['department'],
                            student['academic_year'],
                            student['role']
                        ))
                    else:
                        print(f"User {student['email']} already exists, skipping.")
            else:
                print("Skipping Student insertion: Table 'users' does not exist.")


            # 4. Insert Elections
            if table_exists(cursor, "elections"):
                if admin_id:
                    print("Inserting test elections...")
                    for election in elections:
                        query = "INSERT INTO elections (title, description, start_time, end_time, result_published, created_by) VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(query, (
                            election['title'],
                            election['description'],
                            election['start_time'],
                            election['end_time'],
                            election['result_published'],
                            admin_id
                        ))
                else:
                    print("Skipping Election insertion: Admin user not found/created.")
            else:
                print("Skipping Election insertion: Table 'elections' does not exist.")


            print("\n--- Database seeding completed successfully! ---")

    except Exception as e:
        print(f"\nAn error occurred during seeding: {e}")

if __name__ == "__main__":
    seed_database()
