from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class DashboardFilter:
    from_date: date
    to_date: date
    plazas: tuple[str, ...]

    def validate(self):
        if self.from_date > self.to_date:
            raise ValueError("from_date must not be after to_date")
        allowed = {"TP01", "TP02", "TP03"}
        if any(p not in allowed for p in self.plazas):
            raise ValueError("Unknown plaza")
