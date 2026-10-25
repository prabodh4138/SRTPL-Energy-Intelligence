from .numbers import number

def cumulative_delta(current, previous):
    """
    Returns:
      positive/zero delta -> normal
      None -> insufficient data
      negative -> reset/replacement/anomaly candidate

    A negative delta is NEVER silently converted into consumption.
    """
    c = number(current)
    p = number(previous)

    if c is None or p is None:
        return None, "INSUFFICIENT_DATA"

    delta = c - p

    if delta < 0:
        return delta, "DECREASE"

    return delta, "NORMAL"

def runtime_delta(current, previous):
    return cumulative_delta(current, previous)
