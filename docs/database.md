# Online Voting System — Medium Database Design

# 1. Database Overview

Database Engine:

* MySQL
* InnoDB
* utf8mb4

The schema is designed for:

* normalized relationships
* transaction safety
* referential integrity
* vote consistency
* scalable query handling
* maintainable backend workflows

---

# 2. Core Database Principles

## Referential Integrity

Uses:

* foreign keys
* cascading rules
* unique constraints

---

## Transaction Safety

Critical vote operations use:

* ACID transactions
* rollback support
* atomic commits

---

## Security

Schema supports:

* RBAC
* session validation
* vote uniqueness
* audit verification

---

# 3. Entity Relationships

```text
users
 ├── elections
 ├── candidate_applications
 ├── voting_sessions
 ├── votes
 └── vote_verifications

elections
 ├── candidate_applications
 ├── voting_sessions
 ├── votes
 └── vote_verifications

candidate_applications
 └── votes
```

---

# 4. users Table

## Purpose

Stores students and admins.

## Core Fields

* id
* full_name
* email
* password_hash
* department
* academic_year
* role
* is_active
* created_at

## Business Rules

* email must be unique
* only approved institutional domain allowed
* admin accounts manually created
* passwords stored as hashes only

## Responsibilities

* authentication
* RBAC
* profile management
* election participation ownership

---

# 5. elections Table

## Purpose

Stores election lifecycle data.

## Core Fields

* id
* title
* description
* start_time
* end_time
* result_published
* created_by

## Responsibilities

* election scheduling
* election activation
* election closure
* result publication control

## Election States

Derived dynamically:

```text
UPCOMING
ACTIVE
ENDED
```

Result visibility controlled by:

```text
result_published
```

---

# 6. candidate_applications Table

## Purpose

Stores candidate participation requests.

## Core Fields

* id
* user_id
* election_id
* manifesto
* approval_status
* reviewed_by
* applied_at

## Responsibilities

* candidate application workflow
* admin approval/rejection
* manifesto storage
* election participation tracking

## Business Rules

* one application per election
* rejected candidates cannot reapply same election
* approval required before visibility

## Application States

```text
PENDING
APPROVED
REJECTED
```

---

# 7. voting_sessions Table

## Purpose

Tracks temporary voting access.

## Core Fields

* student_id
* election_id
* started_at
* expires_at
* completed

## Responsibilities

* prevent duplicate sessions
* manage voting expiration
* support controlled vote workflow
* avoid partial vote persistence

## Session Rules

* no new session if election remaining time < 2 minutes
* expired sessions automatically invalidated

---

# 8. votes Table

## Purpose

Stores final committed votes.

## Core Fields

* student_id
* election_id
* candidate_application_id
* voted_at

## Primary Key

```text
(user_id, election_id)
```

This enforces:

```text
one vote per student per election
```

## Responsibilities

* final vote storage
* vote counting
* election result generation
* vote integrity enforcement

## Business Rules

* vote stored only after successful verification
* votes are immutable after commit
* backend + DB both enforce uniqueness

---

# 9. vote_verifications Table

## Purpose

Stores selfie/signature verification evidence.

## Core Fields

* id
* student_id
* election_id
* verification_type
* file_path
* uploaded_at

## Verification Types

```text
SELFIE
SIGNATURE
```

## Responsibilities

* audit evidence storage
* verification linkage
* verification tracking

## Storage Strategy

Files stored in:

```text
/uploads/
```

Database stores only paths.

---

# 10. Vote Transaction Workflow

Critical transaction flow:

```text
1. Validate voting session
2. Insert vote
3. Insert verification
4. Mark session completed
5. Commit transaction
```

If any step fails:

```text
ROLLBACK
```

No partial vote persistence allowed.

---

# 11. Indexing Strategy

Recommended indexes:

* election time lookup
* candidate approval status
* vote counting
* verification lookup
* user role filtering

Optimized for:

* fast result counting
* efficient candidate retrieval
* low-latency vote insertion

---

# 12. Cascade Rules

| Relationship                   | Delete Strategy |
| ------------------------------ | --------------- |
| users → votes                  | CASCADE         |
| users → candidate_applications | CASCADE         |
| elections → votes              | CASCADE         |
| elections → sessions           | CASCADE         |
| reviewed_by                    | SET NULL        |

---

# 13. Upload Structure

```text
uploads/
│
├── selfies/
├── signatures/
├── manifestos/
└── profiles/
```

---

# 14. Database Characteristics

| Property                 | Status |
| ------------------------ | ------ |
| Normalized               | ✅      |
| Transaction-safe         | ✅      |
| Referential integrity    | ✅      |
| RBAC compatible          | ✅      |
| Vote uniqueness enforced | ✅      |
| Session-managed          | ✅      |
| Maintainable             | ✅      |
| Scalable                 | ✅      |
| AI-agent readable        | ✅      |

---

# 15. Future Expansion Compatibility

Supports future additions:

* OTP/email verification
* notifications
* audit logging
* election analytics
* biometric verification
* election categories
* multi-college support
* mobile applications

without major redesign.

---

# 16. Engineering Philosophy

The database architecture intentionally prioritizes:

* clean relational modeling
* practical security
* transaction consistency
* scalable structure
* maintainable workflows

while avoiding:

* unnecessary distributed complexity
* overengineered schemas
* premature optimization
* excessive infrastructure abstraction

The result is a realistic institutional-grade database architecture suitable for:

* production-style backend development
* AI-assisted coding workflows
* scalable future enhancement
* educational deployment
* portfolio-level system design
