class ThresholdProvider:
    """
    Database-backed threshold adapter.

    The application should supply thresholds from energy_master.threshold.
    This class also accepts an in-memory dictionary for local testing.
    """

    def __init__(self, thresholds=None):
        self.thresholds = thresholds or {}

    def get(self, parameter_code, asset_type=None, asset_id=None):
        # Priority: asset-specific -> asset-type -> generic
        for key in (
            (parameter_code, asset_id),
            (parameter_code, asset_type),
            (parameter_code, None),
        ):
            if key in self.thresholds:
                return self.thresholds[key]
        return None

    def evaluate(self, parameter_code, value, asset_type=None, asset_id=None):
        if value is None:
            return None

        t = self.get(parameter_code, asset_type, asset_id)
        if not t:
            return None

        if t.get("critical_min") is not None and value < t["critical_min"]:
            return "CRITICAL"
        if t.get("critical_max") is not None and value > t["critical_max"]:
            return "CRITICAL"
        if t.get("warning_min") is not None and value < t["warning_min"]:
            return "WARNING"
        if t.get("warning_max") is not None and value > t["warning_max"]:
            return "WARNING"
        return None
