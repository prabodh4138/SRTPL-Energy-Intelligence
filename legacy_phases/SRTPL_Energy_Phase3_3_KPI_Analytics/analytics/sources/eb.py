from .cumulative import total_delta
def consumption(readings, field="kwh"):
    return total_delta(readings, field)
def ratio(numerator, denominator):
    if numerator is None or denominator in (None, 0): return None
    return numerator/denominator
def average_pf(readings):
    vals=[r.values.get("pf") for r in readings if r.values.get("pf") is not None]
    return sum(vals)/len(vals) if vals else None
