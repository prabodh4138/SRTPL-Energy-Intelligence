def average(readings, field):
    vals=[r.values.get(field) for r in readings if r.values.get(field) is not None]
    return sum(vals)/len(vals) if vals else None
def maximum(readings, field):
    vals=[r.values.get(field) for r in readings if r.values.get(field) is not None]
    return max(vals) if vals else None
def minimum(readings, field):
    vals=[r.values.get(field) for r in readings if r.values.get(field) is not None]
    return min(vals) if vals else None
def availability_percent(readings):
    if not readings: return None
    good={"RUNNING","ON","NORMAL","AVAILABLE"}
    return sum(str(r.values.get("status","")).upper() in good for r in readings)/len(readings)*100
