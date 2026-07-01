CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(512) NOT NULL,
    role ENUM('STUDENT', 'ADMIN') NOT NULL DEFAULT 'STUDENT',
    department VARCHAR(255),
    academic_year VARCHAR(20),
    profile_picture VARCHAR(255) DEFAULT NULL,
    INDEX idx_users_role (role)
);

CREATE TABLE IF NOT EXISTS elections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status ENUM('UPCOMING', 'ACTIVE', 'ENDED') DEFAULT 'UPCOMING',
    result_published TINYINT(1) DEFAULT 0,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    INDEX idx_elections_start_end (start_time, end_time),
    INDEX idx_elections_published_ended (result_published, end_time),
    INDEX idx_elections_created_at (created_at),
    INDEX idx_elections_created_by (created_by)
);

CREATE TABLE IF NOT EXISTS candidate_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    election_id INT NOT NULL,
    manifesto TEXT,
    approval_status ENUM('PENDING', 'APPROVED', 'REJECTED') DEFAULT 'PENDING',
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (election_id) REFERENCES elections(id),
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id),
    INDEX idx_ca_election_status (election_id, approval_status),
    INDEX idx_ca_user_election (user_id, election_id),
    INDEX idx_ca_approval_status (approval_status),
    INDEX idx_ca_applied_at (applied_at)
);

CREATE TABLE IF NOT EXISTS voting_sessions (
    student_id INT NOT NULL,
    election_id INT NOT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    completed TINYINT(1) DEFAULT 0,
    candidate_application_id INT,
    PRIMARY KEY (student_id, election_id),
    FOREIGN KEY (student_id) REFERENCES users(user_id),
    FOREIGN KEY (election_id) REFERENCES elections(id),
    INDEX idx_vs_student_election_completed (student_id, election_id, completed),
    INDEX idx_vs_expires_at (expires_at)
);

CREATE TABLE IF NOT EXISTS votes (
    voter_id INT NOT NULL,
    election_id INT NOT NULL,
    candidate_id INT NOT NULL,
    voted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (voter_id, election_id),
    FOREIGN KEY (voter_id) REFERENCES users(user_id),
    FOREIGN KEY (election_id) REFERENCES elections(id),
    FOREIGN KEY (candidate_id) REFERENCES candidate_applications(id),
    INDEX idx_votes_election_candidate (election_id, candidate_id),
    INDEX idx_votes_voted_at (voted_at),
    INDEX idx_votes_election_voter (election_id, voter_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    target_type VARCHAR(100),
    target_id INT,
    details JSON,
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_action (action_type),
    INDEX idx_audit_created (created_at),
    INDEX idx_audit_target (target_type, target_id)
);

CREATE TABLE IF NOT EXISTS vote_verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    election_id INT NOT NULL,
    verification_type ENUM('FILE', 'SELFIE', 'SIGNATURE') DEFAULT 'FILE',
    file_path VARCHAR(512),
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(user_id),
    FOREIGN KEY (election_id) REFERENCES elections(id)
);
