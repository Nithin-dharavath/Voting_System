# Online Voting System — Medium Project Overview

# 1. Project Summary

The Online Voting System is a secure web-based election management platform designed for educational institutions. The system digitizes college election workflows and provides secure voting, candidate management, election automation, and result publication.

The platform focuses on:

* secure authentication
* one-time voting
* candidate approval workflows
* vote verification
* automated election timing
* controlled result visibility
* maintainable backend architecture

The system is intentionally designed as a practical institutional-grade application without unnecessary overengineering.

---

# 2. Primary Objectives

Core goals:

* digitize college elections
* prevent duplicate voting
* allow only institutional users
* automate election lifecycle
* secure voting workflow
* support admin-controlled election management
* maintain election integrity
* provide scalable architecture

---

# 3. User Roles

## Student

Capabilities:

* register/login
* participate in elections
* apply as candidate
* cast vote
* upload verification
* view published results

---

## Candidate

Candidate is still a student user.

Capabilities:

* apply for election
* upload manifesto/details
* participate after approval

---

## Admin

Separate admin portal access.

Capabilities:

* create elections
* manage election timing
* approve/reject candidates
* monitor election
* publish results
* review verification uploads

---

# 4. Core Functional Modules

## Authentication Module

Handles:

* student registration/login
* admin login
* JWT authentication
* password hashing
* role-based authorization

---

## Election Module

Handles:

* election creation
* election timing
* election lifecycle management
* result publication control

Election states:

* UPCOMING
* ACTIVE
* ENDED

---

## Candidate Module

Handles:

* candidate applications
* admin approval/rejection
* manifesto handling
* election participation

Application states:

* PENDING
* APPROVED
* REJECTED

Rejected candidates cannot reapply for the same election.

---

## Voting Module

Handles:

* voting sessions
* vote submission
* duplicate vote prevention
* session expiration
* vote confirmation workflow

Voting rules:

* one student → one vote per election
* voting allowed only during active election
* no new voting sessions if election remaining time < 2 minutes

---

## Verification Module

Handles:

* selfie uploads
* signature uploads
* verification storage
* verification linking

Verification acts as audit evidence.

---

## Result Module

Handles:

* vote counting
* result generation
* result publication

Students cannot view live vote counts.
Results become visible only after admin publication.

---

# 5. User Flows

## Student Flow

```text
Landing Page
    ↓
Register/Login
    ↓
Dashboard
    ↓
View Election
    ↓
View Candidates
    ↓
Vote
    ↓
Verification Upload
    ↓
Vote Success
```

---

## Candidate Flow

```text
Dashboard
    ↓
Apply For Election
    ↓
Pending Approval
    ↓
Approved/Rejected
```

---

## Admin Flow

```text
Admin Login
    ↓
Admin Dashboard
    ↓
Create Election
    ↓
Review Candidates
    ↓
Approve/Reject
    ↓
Monitor Election
    ↓
Publish Results
```

---

# 6. Security Design

## Authentication Security

* JWT-based authentication
* hashed passwords
* protected admin routes
* role-based access control

---

## Voting Security

* backend vote validation
* DB uniqueness enforcement
* transaction-safe vote commits
* session expiration handling
* protected election timing

---

# 7. Technology Stack

| Layer          | Technology            |
| -------------- | --------------------- |
| Frontend       | HTML, CSS, JavaScript |
| Backend        | FastAPI               |
| Database       | MySQL                 |
| Authentication | JWT                   |
| Deployment     | Docker + AWS          |
| File Storage   | Local Upload Storage  |

---

# 8. System Architecture

```text
Frontend (HTML/CSS/JS)
        ↓
FastAPI Backend
        ↓
Business Logic Layer
        ↓
MySQL Database
```

Architecture Type:

```text
Modular Monolithic REST Architecture
```

---

# 9. Backend Folder Structure

```text
app/
│
├── auth/
├── users/
├── elections/
├── candidates/
├── votes/
├── admin/
├── middleware/
├── database/
├── models/
├── schemas/
└── core/
```

---

# 10. Deployment Design

## Docker Components

```text
Frontend Container
Backend Container
MySQL Container
Uploads Volume
```

Deployment Target:

* AWS EC2

---

# 11. Non-Functional Goals

## Reliability

* rollback-safe voting
* controlled session handling
* transaction-safe commits

## Performance

Optimized for:

* 100–1000 users
* fast vote insertion
* efficient result counting

## Maintainability

* modular architecture
* scalable backend structure
* clean separation of concerns

---

# 12. Future Expansion

Possible future additions:

* OTP verification
* biometric verification
* notifications
* analytics dashboard
* audit logging
* mobile application
* election categories

---

# 13. Engineering Philosophy

The project intentionally prioritizes:

* practical architecture
* maintainable structure
* realistic security
* scalable workflows
* clean backend design

while avoiding:

* unnecessary microservices
* premature optimization
* overengineered infrastructure
* unnecessary distributed systems

The result is a realistic institutional-grade online voting platform suitable for:

* portfolio projects
* academic deployment
* AI-assisted development
* backend architecture learning
* future production expansion
