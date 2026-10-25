from datetime import datetime, timezone
from .models import KPIResult

class KPIEngine:
    def __init__(self, registry, calculation_version="3.3.0"):
        self.registry = registry
        self.calculation_version = calculation_version

    def calculate(self, kpi_code, readings, **kwargs):
        definition = self.registry.get(kpi_code)
        valid = [r for r in readings if r.validation_status == "VALID"]
        now = datetime.now(timezone.utc)
        start = kwargs.get("period_start", now)
        end = kwargs.get("period_end", now)
        ids = [r.source_reading_id for r in valid if r.source_reading_id]
        if not valid:
            return KPIResult(definition.code, definition.name, kwargs.get("asset_id"),
                             kwargs.get("plaza_id"), start, end, None, definition.unit,
                             "INSUFFICIENT_DATA", self.calculation_version, 0, [], "No valid source readings.")
        value = definition.calculator(valid, **kwargs)
        if isinstance(value, tuple):
            value, status = value
        else:
            status = "CALCULATED"
        return KPIResult(definition.code, definition.name, kwargs.get("asset_id"),
                         kwargs.get("plaza_id"), start, end, value, definition.unit,
                         status, self.calculation_version, len(valid), ids)
