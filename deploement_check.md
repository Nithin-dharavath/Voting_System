# Deployment Checklist & Roadmap

> **Target:** AWS Free Tier (EC2 + RDS + S3 + ECR)
> **Timeline:** This week
> **Total Steps:** 22

---

## Phase 1: Pre-Production Code Changes

> Goal: Harden the app for production before touching AWS.

### 1.1 — Enforce JWT_SECRET in production
- [ ] **File:** `config.py`
- [ ] Add validation: raise `ValueError` on startup if `JWT_SECRET` is the default value and `ENVIRONMENT=production`
- [ ] Add `S3_BUCKET`, `S3_REGION` fields to `Settings`
- [ ] **Done?**

### 1.2 — Add security headers middleware
- [ ] **File:** `middleware.py`
- [ ] Create `SecurityHeadersMiddleware` class
- [ ] Headers: `Strict-Transport-Security`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Content-Security-Policy`
- [ ] Register middleware in `app.py`
- [ ] **Done?**

### 1.3 — Add S3 upload support
- [ ] **Files:** `services/file_service.py`, `requirements.txt`, `config.py`
- [ ] Add `boto3` to `requirements.txt`
- [ ] Create `S3Storage` class with `upload_file()` and `get_file_url()` methods
- [ ] Keep local storage as fallback for development
- [ ] Gate S3 usage on `ENVIRONMENT=production`
- [ ] **Done?**

### 1.4 — Harden CORS for production
- [ ] **File:** `app.py`
- [ ] Set strict CORS origins in production (EC2 IP/domain)
- [ ] Allow `*` only in development
- [ ] **Done?**

### 1.5 — Multi-stage Docker build
- [ ] **File:** `Dockerfile`
- [ ] Stage 1 (builder): Install deps, compile
- [ ] Stage 2 (runtime): `python:3.11-slim`, copy only artifacts
- [ ] Add `HEALTHCHECK` instruction
- [ ] Run as non-root user
- [ ] **Done?**

### 1.6 — Production docker-compose
- [ ] **File:** `docker-compose.prod.yml`
- [ ] Services: `app`, `worker`, `nginx`
- [ ] No DB service (uses RDS externally)
- [ ] Read env from `.env.production` or Secrets Manager
- [ ] **Done?**

### 1.7 — Nginx reverse proxy config
- [ ] **File:** `nginx.conf`
- [ ] Listen on 80 → redirect to 443
- [ ] Listen on 443 → proxy_pass to `app:8000`
- [ ] SSL cert paths (Let's Encrypt)
- [ ] Static file caching headers
- [ ] Rate limiting rules
- [ ] **Done?**

### 1.8 — EC2 user-data script
- [ ] **File:** `user-data.sh`
- [ ] Install Docker + docker-compose
- [ ] Install nginx + certbot
- [ ] Create `/app` directory
- [ ] Set up certbot auto-renew cron job
- [ ] **Done?**

### 1.9 — Update env templates
- [ ] **File:** `.env.example`
- [ ] Add: `S3_BUCKET`, `S3_REGION`, `ENVIRONMENT`
- [ ] Remove default secrets
- [ ] Add comments for production-only vars
- [ ] **Done?**

### 1.10 — Local verification
- [ ] Run: `ruff check .` — zero errors
- [ ] Run: `mypy app.py` — no type errors
- [ ] Run: `pytest -m "not integration" --cov` — all green
- [ ] Run: `alembic upgrade head` on a fresh DB — clean apply
- [ ] Run: `docker build -t voting-system .` — builds without error
- [ ] **Done?**

---

## Phase 2: AWS Infrastructure (via MCP)

> Goal: Create all AWS resources using MCP server.

### 2.1 — RDS MySQL Instance
- [ ] Engine: MySQL 8.0
- [ ] Class: `db.t2.micro` (free tier)
- [ ] Storage: 20GB gp2
- [ ] Auto-backups: 7 days retention
- [ ] Security group: allow port 3306 from EC2 security group only
- [ ] **Done?**

### 2.2 — S3 Bucket
- [ ] Bucket name: `voting-system-uploads-<unique-suffix>`
- [ ] Block all public access
- [ ] Enable CORS for EC2 origin
- [ ] Lifecycle rule: transition to Glacier after 90 days
- [ ] **Done?**

### 2.3 — IAM Role for EC2
- [ ] Trust policy: EC2 service
- [ ] Attach policies: `AmazonS3FullAccess`, `AmazonEC2ReadOnly`
- [ ] Create instance profile
- [ ] **Done?**

### 2.4 — ECR Repository
- [ ] Repository name: `voting-system`
- [ ] Tag immutability: enabled
- [ ] Scan on push: enabled
- [ ] **Done?**

### 2.5 — Security Group for EC2
- [ ] Inbound: port 80 (HTTP, 0.0.0.0/0)
- [ ] Inbound: port 443 (HTTPS, 0.0.0.0/0)
- [ ] Inbound: port 22 (SSH, your IP only)
- [ ] Outbound: all traffic
- [ ] **Done?**

### 2.6 — EC2 Instance
- [ ] AMI: Amazon Linux 2023
- [ ] Type: `t2.micro` (free tier)
- [ ] IAM role: attach from 2.3
- [ ] Security group: attach from 2.5
- [ ] User-data: use `user-data.sh`
- [ ] Key pair: create for SSH access
- [ ] **Done?**

### 2.7 — Elastic IP
- [ ] Allocate Elastic IP
- [ ] Associate with EC2 instance
- [ ] **Done?**

### 2.8 — Secrets Manager
- [ ] Store: `DB_PASSWORD` — the RDS master password
- [ ] Store: `JWT_SECRET` — a strong random secret
- [ ] Store: `SENTRY_DSN` — optional error tracking DSN
- [ ] **Done?**

---

## Phase 3: CI/CD Pipeline

> Goal: Automate deploy from GitHub → EC2.

### 3.1 — Extend GitHub Actions workflow
- [ ] **File:** `.github/workflows/ci.yml`
- [ ] Add `deploy` job after `docker-build`
- [ ] Steps: configure AWS creds → login to ECR → build & push → run migrations → SSH deploy
- [ ] Use `appleboy/ssh-action` for EC2 commands
- [ ] Health check after deploy
- [ ] **Done?**

### 3.2 — Add GitHub Secrets
- [ ] `AWS_DEPLOY_ROLE` — IAM role ARN for GitHub Actions
- [ ] `EC2_HOST` — Elastic IP address
- [ ] `EC2_SSH_KEY` — private key for EC2
- [ ] `AWS_REGION` — e.g. `us-east-1`
- [ ] `ECR_REGISTRY` — ECR registry URL
- [ ] `ECR_REPO` — ECR repository URL
- [ ] **Done?**

### 3.3 — Test the pipeline
- [ ] Push a trivial change to `master`
- [ ] Watch GitHub Actions run: lint → test → build → push → deploy
- [ ] Verify: `curl https://<EC2_IP>/health` returns 200
- [ ] **Done?**

---

## Phase 4: First Deploy & Verify

> Goal: Initial manual deploy to seed and verify everything works end-to-end.

### 4.1 — Push code trigger
- [ ] Push to `master`
- [ ] Wait for GitHub Actions to complete
- [ ] Verify image pushed to ECR
- [ ] **Done?**

### 4.2 — SSH into EC2
- [ ] `ssh -i <key.pem> ec2-user@<ELASTIC_IP>`
- [ ] Verify Docker is running: `docker ps`
- [ ] Pull latest image: `docker compose -f docker-compose.prod.yml pull`
- [ ] Start services: `docker compose -f docker-compose.prod.yml up -d`
- [ ] **Done?**

### 4.3 — Run database migrations
- [ ] `docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head`
- [ ] Verify tables exist in RDS
- [ ] **Done?**

### 4.4 — Seed database
- [ ] `docker compose -f docker-compose.prod.yml run --rm app python database/seed.py`
- [ ] Verify admin + student accounts exist
- [ ] **Done?**

### 4.5 — Initial SSL certificate
- [ ] SSH into EC2
- [ ] `sudo certbot --nginx --non-interactive --agree-tos -m <email> -d <ELASTIC_IP>`
- [ ] Verify HTTPS works: `curl https://<ELASTIC_IP>/health`
- [ ] **Done?**

### 4.6 — End-to-end functional test
- [ ] Open `https://<ELASTIC_IP>` in browser
- [ ] Login as admin — dashboard loads
- [ ] Create an election
- [ ] Login as student — see elections list
- [ ] Apply as candidate
- [ ] Admin approves candidate
- [ ] Vote in election
- [ ] Upload verification (selfie/signature)
- [ ] View results
- [ ] Export results (CSV/PDF)
- [ ] **Done?**

---

## Summary

```
Phase 1: Pre-Production Code Changes  [  /10 ]
Phase 2: AWS Infrastructure           [  /8  ]
Phase 3: CI/CD Pipeline               [  /3  ]
Phase 4: First Deploy & Verify        [  /6  ]
─────────────────────────────────────────────
Total:                                [  /27 ]
```
