# Online Voting System — Database Design

## Overview

* MySQL + InnoDB + utf8mb4
* Secure, scalable, and transaction-safe design

## Main Tables

### users

Stores students and admins.

* id
* full_name
* email
* password_hash
* role
* department
* academic_year

### elections

Stores election details.

* id
* title
* description
* start_time
* end_time
* result_published
* created_by

### candidate_applications

Stores candidate requests.

* id
* user_id
* election_id
* manifesto
* approval_status
* reviewed_by

### voting_sessions

Tracks temporary voting access.

* student_id
* election_id
* started_at
* expires_at
* completed

### votes

Stores final votes.

* student_id
* election_id
* candidate_application_id
* voted_at

**Constraint:** One vote per student per election.

### vote_verifications

Stores verification evidence.

* id
* student_id
* election_id
* verification_type
* file_path

## Core Features

* Foreign Keys
* Unique Constraints
* RBAC Support
* Vote Uniqueness
* Transaction Safety
* Audit Verification

## Vote Workflow

```text
1. Validate Session
2. Insert Vote
3. Insert Verification
4. Complete Session
5. Commit Transaction

If any step fails:
ROLLBACK
```

## Upload Structure

```text
uploads/
├── selfies/
├── signatures/
├── manifestos/
└── profiles/
```

## Benefits

* Normalized Database
* Secure Architecture
* Transaction-Safe
* Scalable Design
* Maintainable Structure
* Future Expansion Ready

## Future Enhancements

* OTP Verification
* Notifications
* Audit Logs
* Election Analytics
* Biometric Verification
* Mobile Application Support

## Goal

Build a secure and reliable online voting system with strong vote integrity, efficient management, and future scalability.
