# Online Voting System

A secure, web-based election management platform for educational institutions built with **FastAPI**, **Jinja2**, and **MySQL**.

## Features

- **Authentication** — JWT-based login/registration with role-based access (STUDENT, ADMIN)
- **Election Management** — Create, edit, and manage elections with automated lifecycle (UPCOMING → ACTIVE → ENDED)
- **Candidate Applications** — Students can apply; admins approve or reject with PENDING / APPROVED / REJECTED workflow
- **Secure Voting** — One vote per student per election with session-based voting and duplicate prevention
- **Vote Verification** — Upload selfies or signatures as audit evidence per vote
- **Result Publication** — Admin-controlled result publishing; students see results only after publication
- **Admin Dashboard** — Centralized election oversight, candidate review, and result management

## Tech Stack

| Layer          | Technology            |
| -------------- | --------------------- |
| Frontend       | HTML, CSS, JavaScript (Jinja2 templates) |
| Backend        | FastAPI (Python)      |
| Database       | MySQL                 |
| Authentication | JWT (PyJWT)           |
| File Storage   | Local upload storage  |

## Getting Started

### Prerequisites

- Python 3.10+
- MySQL server

### Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd Voting_System

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
# Edit .env with your MySQL credentials:
#   DB_HOST=localhost
#   DB_PORT=3306
#   DB_NAME=voting_system
#   DB_USER=root
#   DB_PASSWORD=your_password

# 5. Seed the database
python database/seed.py

# 6. Run the development server
uvicorn app:app --reload
```

The application will be available at `http://localhost:8000`.

### Seed Accounts

| Role    | Email               | Password            |
| ------- | ------------------- | ------------------- |
| Admin   | admin@college.edu   | adminpassword123    |
| Student | alice@college.edu   | studentpassword123  |
| Student | bob@college.edu     | studentpassword123  |
| Student | charlie@college.edu | studentpassword123  |
| Student | diana@college.edu   | studentpassword123  |

## Project Structure

```
Voting_System/
├── app.py                 # FastAPI application entrypoint
├── database/
│   ├── connection.py      # MySQL connection utility
│   ├── seed.py            # Database seeding script
│   └── create_admin.py    # Admin account creation
├── templates/             # Jinja2 HTML templates
│   ├── base.html          # Base layout
│   └── partials/          # Reusable template fragments
├── static/
│   ├── css/               # Stylesheets
│   └── js/                # Client-side scripts
├── uploads/               # User-uploaded files (profiles, verifications)
├── tests/                 # Pytest test suite
├── docs/                  # Documentation
└── workflow/              # Development phase notes
```

## Testing

```bash
pytest
```

## License

MIT
