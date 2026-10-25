from .status import can_transition

class ExceptionService:
    def validate_transition(self, current_status, target_status):
        if not can_transition(current_status, target_status):
            raise ValueError(
                f"Invalid exception status transition: {current_status} -> {target_status}"
            )

    def resolve(self, repository, exception_id, current_status, note, user):
        self.validate_transition(current_status, "RESOLVED")
        if not note or not note.strip():
            raise ValueError("Resolution note is mandatory.")
        return repository.update_status(
            exception_id, "RESOLVED",
            note=f"{note.strip()} | resolved_by={user}"
        )

    def accept_exception(self, repository, exception_id, current_status, note, user):
        self.validate_transition(current_status, "ACCEPTED_EXCEPTION")
        if not note or not note.strip():
            raise ValueError("Acceptance reason is mandatory.")
        return repository.update_status(
            exception_id, "ACCEPTED_EXCEPTION",
            note=f"{note.strip()} | accepted_by={user}"
        )
