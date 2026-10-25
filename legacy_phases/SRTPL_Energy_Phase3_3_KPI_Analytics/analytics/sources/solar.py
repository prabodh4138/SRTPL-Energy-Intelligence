from .cumulative import total_delta
def daily_generation(readings):
    return total_delta(readings, "cumulative_kwh")
