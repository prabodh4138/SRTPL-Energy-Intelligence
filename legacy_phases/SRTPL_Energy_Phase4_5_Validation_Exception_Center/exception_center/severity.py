ORDER = {"INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}

def sort_severity(values):
    return sorted(values, key=lambda x: ORDER.get(x, 0), reverse=True)
