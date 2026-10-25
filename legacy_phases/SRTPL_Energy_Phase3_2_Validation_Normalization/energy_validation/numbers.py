def number(value):
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None

def valid_pf(value):
    x = number(value)
    return x is not None and 0 <= x <= 1.0

def percent_imbalance(values):
    nums = [number(v) for v in values]
    nums = [v for v in nums if v is not None]
    if not nums:
        return None
    avg = sum(nums) / len(nums)
    if avg == 0:
        return None
    return max(abs(v - avg) for v in nums) / abs(avg) * 100
