from dataclasses import dataclass
@dataclass
class EnergyBalance:
    eb_kwh: float|None
    dg_kwh: float|None
    solar_kwh: float|None
    @property
    def recorded_input(self):
        return sum(v for v in (self.eb_kwh,self.dg_kwh,self.solar_kwh) if v is not None) or None
    @property
    def solar_contribution_percent(self):
        return None if self.recorded_input in (None,0) or self.solar_kwh is None else self.solar_kwh/self.recorded_input*100
    @property
    def dg_contribution_percent(self):
        return None if self.recorded_input in (None,0) or self.dg_kwh is None else self.dg_kwh/self.recorded_input*100
