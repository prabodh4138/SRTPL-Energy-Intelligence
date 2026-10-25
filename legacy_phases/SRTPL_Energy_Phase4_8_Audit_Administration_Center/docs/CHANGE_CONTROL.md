# Change Control

Master data and configuration should not be edited directly in production.

Workflow:
PENDING → APPROVED → APPLIED

or:
PENDING → REJECTED/CANCELLED

A request must contain:
- entity
- entity ID
- change type
- old value
- proposed value
- reason
- requester
- approver
- timestamps

The original data is never lost. Changes create an audit trail.
