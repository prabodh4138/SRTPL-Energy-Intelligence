class AuditService:
    def build_event(self, actor_user_id, action, entity_type=None,
                    entity_id=None, old_value=None, new_value=None,
                    reason=None):
        return {
            "actor_user_id": actor_user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
        }

    def require_reason(self, reason):
        if not reason or not reason.strip():
            raise ValueError("A reason is mandatory for this administrative action.")
