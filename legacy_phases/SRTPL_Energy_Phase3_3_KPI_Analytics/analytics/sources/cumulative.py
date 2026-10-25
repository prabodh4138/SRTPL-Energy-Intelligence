def delta(current, previous):
    if current is None or previous is None:
        return None, "INSUFFICIENT_DATA"
    if current < previous:
        return None, "CUMULATIVE_DECREASE"
    return current - previous, "OK"

def total_delta(readings, field):
    ordered = sorted(readings, key=lambda r: r.reading_at)
    if len(ordered) < 2:
        return None, "INSUFFICIENT_DATA"
    total = 0.0
    for prev, cur in zip(ordered, ordered[1:]):
        d, status = delta(cur.values.get(field), prev.values.get(field))
        if status != "OK":
            return None, status
        total += d
    return total, "OK"
