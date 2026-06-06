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
        "role": "ADMIN",
        "profile_picture": "/uploads/profiles/admin_default.jpg"
    }

    student_users = [
        {
            "full_name": "Alice Student",
            "email": "alice@college.edu",
            "password": "studentpassword123",
            "department": "Computer Science",
            "academic_year": "2025-26",
            "role": "STUDENT",
            "profile_picture": "/uploads/profiles/alice.jpg"
        },
        {
            "full_name": "Bob Student",
            "email": "bob@college.edu",
            "password": "studentpassword123",
            "department": "Electrical Engineering",
            "academic_year": "2025-26",
            "role": "STUDENT",
            "profile_picture": None
        },
        {
            "full_name": "Charlie Student",
            "email": "charlie@college.edu",
            "password": "studentpassword123",
            "department": "Mathematics",
            "academic_year": "2025-26",
            "role": "STUDENT",
            "profile_picture": "/uploads/profiles/charlie.jpg"
        },
        {
            "full_name": "Diana Student",
            "email": "diana@college.edu",
            "password": "studentpassword123",
            "department": "Physics",
            "academic_year": "2025-26",
            "role": "STUDENT",
            "profile_picture": None
        }
    ]

    now = datetime.datetime.now()

    elections = [
        {
            "title": "General Secretary Election 2026",
            "description": "Election for the General Secretary position.",
            "start_time": now + datetime.timedelta(days=7),
            "end_time": now + datetime.timedelta(days=8),
            "status": "UPCOMING",
            "result_published": 0
        },
        {
            "title": "Student Council President 2026",
            "description": "Election for the Student Council President.",
            "start_time": now - datetime.timedelta(days=1),
            "end_time": now + datetime.timedelta(days=1),
            "status": "ACTIVE",
            "result_published": 0
        },
        {
            "title": "Sports Captain 2025",
            "description": "Election for the Sports Captain position.",
            "start_time": now - datetime.timedelta(days=90),
            "end_time": now - datetime.timedelta(days=89),
            "status": "ENDED",
            "result_published": 0
        },
        {
            "title": "Cultural Fest Lead 2025",
            "description": "Election for the Cultural Fest Lead.",
            "start_time": now - datetime.timedelta(days=60),
            "end_time": now - datetime.timedelta(days=59),
            "status": "ENDED",
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
                cursor.execute("SELECT user_id FROM users WHERE email = %s", (admin_user['email'],))
                row = cursor.fetchone()
                if not row:
                    hashed_pw = generate_password_hash(admin_user['password'])
                    query = "INSERT INTO users (full_name, email, password_hash, department, academic_year, role, profile_picture) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(query, (
                        admin_user['full_name'],
                        admin_user['email'],
                        hashed_pw,
                        admin_user['department'],
                        admin_user['academic_year'],
                        admin_user['role'],
                        admin_user['profile_picture']
                    ))
                    admin_id = cursor.lastrowid
                else:
                    admin_id = row['user_id']
            else:
                print("Skipping User insertion: Table 'users' does not exist.")
                admin_id = None

            # 3. Insert Student Users
            student_ids = []
            if table_exists(cursor, "users"):
                for student in student_users:
                    print(f"Ensuring student user exists: {student['email']}...")
                    cursor.execute("SELECT user_id FROM users WHERE email = %s", (student['email'],))
                    row = cursor.fetchone()
                    if not row:
                        hashed_pw = generate_password_hash(student['password'])
                        query = "INSERT INTO users (full_name, email, password_hash, department, academic_year, role, profile_picture) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(query, (
                            student['full_name'],
                            student['email'],
                            hashed_pw,
                            student['department'],
                            student['academic_year'],
                            student['role'],
                            student['profile_picture']
                        ))
                        student_ids.append(cursor.lastrowid)
                    else:
                        print(f"User {student['email']} already exists, skipping.")
                        student_ids.append(row['user_id'])
            else:
                print("Skipping Student insertion: Table 'users' does not exist.")

            # 4. Insert Elections
            election_ids = []
            if table_exists(cursor, "elections"):
                if admin_id:
                    print("Inserting test elections...")
                    for election in elections:
                        query = "INSERT INTO elections (title, description, start_time, end_time, status, result_published, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(query, (
                            election['title'],
                            election['description'],
                            election['start_time'],
                            election['end_time'],
                            election['status'],
                            election['result_published'],
                            admin_id
                        ))
                        election_ids.append(cursor.lastrowid)
                else:
                    print("Skipping Election insertion: Admin user not found/created.")
            else:
                print("Skipping Election insertion: Table 'elections' does not exist.")

            # 5. Insert Candidate Applications for testing
            if table_exists(cursor, "candidate_applications") and student_ids and election_ids:
                print("Inserting test candidate applications...")
                # Mix of statuses to test all views
                # (user_id, election_id, manifesto, status, reviewed_by)
                apps = [
                    (student_ids[0], election_ids[0], "I will bring transparency and efficiency to the student body.", "PENDING", None),
                    (student_ids[1], election_ids[0], "Experienced leader with a vision for lauter growth.", "PENDING", None),
                    (student_ids[2], election_ids[0], "Focused on academic excellence and student support.", "APPROVED", admin_id),
                    (student_ids[3], election_ids[0], "Passion for arts and culture on campus.", "REJECTED", admin_id),
                    (student_ids[0], election_ids[1], "Bringing a new perspective to the council.", "APPROVED", admin_id),
                    (student_ids[1], election_ids[1], "Dedicated to improving campus facilities.", "REJECTED", admin_id),
                ]

                query = "INSERT INTO candidate_applications (user_id, election_id, manifesto, approval_status, reviewed_by) VALUES (%s, %s, %s, %s, %s)"
                cursor.executemany(query, apps)

                # Approved candidates for the two ENDED elections so results pages
                # have tallies to display.
                # election_ids[2] = Sports Captain 2025 (ENDED, NOT published) -> shows Publish button
                # election_ids[3] = Cultural Fest Lead 2025 (ENDED, published) -> shows badge
                ended_apps = [
                    (student_ids[0], election_ids[2], "Promoting athletics and team spirit across the campus.", "APPROVED", admin_id),
                    (student_ids[1], election_ids[2], "Building inclusive sports programs for every student.", "APPROVED", admin_id),
                    (student_ids[2], election_ids[2], "Driving excellence in competitive and recreational sports.", "APPROVED", admin_id),
                    (student_ids[3], election_ids[3], "A vibrant cultural calendar that reflects every student voice.", "APPROVED", admin_id),
                    (student_ids[0], election_ids[3], "Showcasing talent through festivals, workshops, and showcases.", "APPROVED", admin_id),
                ]
                cursor.executemany(query, ended_apps)

                # 6. Insert vote_verifications + votes for the ENDED elections
                # so the results pages have real tallies to count.
                if table_exists(cursor, "vote_verifications") and table_exists(cursor, "votes"):
                    print("Seeding votes and verifications for ENDED elections...")

                    # Look up candidate_application ids per ENDED election, ordered
                    # so vote distributions align with the candidate list order.
                    def approved_cap_ids(election_id):
                        cursor.execute(
                            "SELECT id FROM candidate_applications WHERE election_id = %s AND approval_status = 'APPROVED' ORDER BY id",
                            (election_id,)
                        )
                        return [row['id'] for row in cursor.fetchall()]

                    sports_cap_ids = approved_cap_ids(election_ids[2])
                    cultural_cap_ids = approved_cap_ids(election_ids[3])

                    # Vote counts per candidate (one slot per approved candidate).
                    # We have 4 student voters; each can cast at most one vote
                    # per election, so totals per election are capped at 4.
                    # Sports Captain 2025 -> 3 candidates, totals 4
                    # Cultural Fest Lead 2025 -> 2 candidates, totals 4
                    distributions = {
                        election_ids[2]: [2, 1, 1],
                        election_ids[3]: [2, 2],
                    }
                    cap_ids_by_election = {
                        election_ids[2]: sports_cap_ids,
                        election_ids[3]: cultural_cap_ids,
                    }

                    verifications = []
                    votes = []
                    voted_at = now - datetime.timedelta(days=89)
                    voter_pool = list(student_ids)
                    voter_cursor = 0

                    for election_id, cap_ids in cap_ids_by_election.items():
                        for cap_id, count in zip(cap_ids, distributions[election_id]):
                            for _ in range(count):
                                voter_id = voter_pool[voter_cursor % len(voter_pool)]
                                voter_cursor += 1
                                verifications.append((
                                    voter_id, election_id, "FILE",
                                    f"/uploads/verifications/v_{voter_id}_{election_id}.pdf",
                                    voted_at,
                                ))
                                votes.append((voter_id, election_id, cap_id, voted_at))

                    if verifications:
                        cursor.executemany(
                            "INSERT INTO vote_verifications (student_id, election_id, verification_type, file_path, uploaded_at) VALUES (%s, %s, %s, %s, %s)",
                            verifications
                        )
                    if votes:
                        cursor.executemany(
                            "INSERT INTO votes (voter_id, election_id, candidate_id, voted_at) VALUES (%s, %s, %s, %s)",
                            votes
                        )

            print("\n--- Database seeding completed successfully! ---")

    except Exception as e:
        print(f"\nAn error occurred during seeding: {e}")

if __name__ == "__main__":
    seed_database()
