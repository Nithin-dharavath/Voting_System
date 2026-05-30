this the table i have craeted in my database : 

CREATE TABLE candidate_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    election_id INT NOT NULL,

    manifesto TEXT NOT NULL,

    approval_status ENUM(
        'PENDING',
        'APPROVED',
        'REJECTED'
    ) NOT NULL DEFAULT 'PENDING',

    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    reviewed_by INT NULL,

    CONSTRAINT fk_candidate_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_candidate_election
        FOREIGN KEY (election_id)
        REFERENCES elections(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_candidate_reviewer
        FOREIGN KEY (reviewed_by)
        REFERENCES users(id)
        ON DELETE SET NULL,

    UNIQUE KEY unique_candidate_application (
        user_id,
        election_id
    )
);