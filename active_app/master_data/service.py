from .validation import (
    validate_plaza, validate_asset,
    validate_effective_dates, validate_threshold
)

class MasterDataService:
    def validate_plaza(self, code, name):
        validate_plaza(code, name)

    def validate_asset(self, asset_code, asset_type):
        validate_asset(asset_code, asset_type)

    def validate_dates(self, start, end=None):
        validate_effective_dates(start, end)

    def validate_threshold(self, warning, critical):
        validate_threshold(warning, critical)

    def require_change_control(self, action):
        # All production master/config mutations must flow through
        # Phase 4.8 change request and protected RPCs.
        return {
            "action": action,
            "requires_change_request": True,
            "requires_audit": True,
        }
