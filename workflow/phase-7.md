# Phase 7: Setup Admin Candidate Approval

## Goal

Allow admins to review, approve, or reject candidate applications and ensure that only approved candidates are eligible for voting.

## To Do

* Create candidate review page `/admin/candidates`.
* Create election candidate page `/admin/elections/:id/candidates`.
* Create pending candidate applications route `GET /admin/candidates/pending`.
* Create candidate approval route `PUT /admin/candidates/:id/approve`.
* Create candidate rejection route `PUT /admin/candidates/:id/reject`.
* Update candidate application status handling:

  * `PENDING`
  * `APPROVED`
  * `REJECTED`

* Allow admins to view candidate details and manifestos.
* Record reviewer information when approving or rejecting applications.
* Ensure only `APPROVED` candidates are available for voting.
* Test pending candidate listing.
* Test candidate approval workflow.
* Test candidate rejection workflow.
* Test approved candidate visibility in elections.
* Restrict candidate review actions to admins only.

## End Result

Admins can review candidate applications, approve or reject candidates, and only approved candidates are eligible for voting.
