-- Performance Indexes for Voting System
-- Run this if you are not using Alembic migrations
-- Generated: 2026-07-02

-- Users
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);

-- Elections
CREATE INDEX IF NOT EXISTS idx_elections_start_end ON elections (start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_elections_published_ended ON elections (result_published, end_time);
CREATE INDEX IF NOT EXISTS idx_elections_created_at ON elections (created_at);
CREATE INDEX IF NOT EXISTS idx_elections_created_by ON elections (created_by);

-- Candidate Applications
CREATE INDEX IF NOT EXISTS idx_ca_election_status ON candidate_applications (election_id, approval_status);
CREATE INDEX IF NOT EXISTS idx_ca_user_election ON candidate_applications (user_id, election_id);
CREATE INDEX IF NOT EXISTS idx_ca_approval_status ON candidate_applications (approval_status);
CREATE INDEX IF NOT EXISTS idx_ca_applied_at ON candidate_applications (applied_at);

-- Votes
CREATE INDEX IF NOT EXISTS idx_votes_election_candidate ON votes (election_id, candidate_id);
CREATE INDEX IF NOT EXISTS idx_votes_voted_at ON votes (voted_at);
CREATE INDEX IF NOT EXISTS idx_votes_election_voter ON votes (election_id, voter_id);

-- Voting Sessions
CREATE INDEX IF NOT EXISTS idx_vs_student_election_completed ON voting_sessions (student_id, election_id, completed);
CREATE INDEX IF NOT EXISTS idx_vs_expires_at ON voting_sessions (expires_at);
