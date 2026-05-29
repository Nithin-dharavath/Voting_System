# Phase 6: Setup Candidate Application

## Goal

Allow students to apply as candidates for elections and track their application status.

## To Do

* Create candidate apply page `/student/elections/:id/apply`.
* Create candidate status page `/student/candidate-status`.
* Create `candidate_applications` table.
* Add candidate application fields:

  * `id`
  * `user_id`
  * `election_id`
  * `manifesto`
  * `approval_status`
  * `applied_at`
  * `reviewed_by`
* Add candidate approval statuses:

  * `PENDING`
  * `APPROVED`
  * `REJECTED`
* Create candidate application route `POST /candidates/apply`.
* Create my applications route `GET /candidates/my-applications`.
* Block duplicate applications:

  * One student can apply only once per election.
* Test candidate application submission.
* Test candidate application listing.
* Test duplicate application prevention.
* Test candidate status display.

## End Result

Students can apply as candidates for elections and view their application status successfully.
