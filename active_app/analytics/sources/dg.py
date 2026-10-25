from .cumulative import total_delta
def generation(readings):
    return total_delta(readings, "cumulative_kwh")
def runtime_hours(readings):
    return total_delta(readings, "running_hours")
def kwh_per_hour(generation_kwh, runtime_hours_value):
    if generation_kwh is None or runtime_hours_value in (None, 0):
        return None
    return generation_kwh / runtime_hours_value
def average_pf(readings):
    vals=[r.values.get("pf") for r in readings if r.values.get("pf") is not None]
    return sum(vals)/len(vals) if vals else None
def phase_imbalance(values):
    vals=[float(v) for v in values if v is not None]
    if len(vals)!=3: return None
    avg=sum(vals)/3
    return None if avg==0 else max(abs(v-avg) for v in vals)/avg*100
def voltage_imbalance_percent(reading):
    return phase_imbalance([reading.values.get(k) for k in ("voltage_ry","voltage_yb","voltage_br")])
def current_imbalance_percent(reading):
    return phase_imbalance([reading.values.get(k) for k in ("current_r","current_y","current_b")])
