from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class PlazaFilter:
    plaza: str
    from_date: date
    to_date: date

    def validate(self):
        if not self.plaza:
            raise ValueError("Plaza is required.")
        if self.from_date > self.to_date:
            raise ValueError("From date cannot be after To date.")
