def phase_imbalance(values):
    vals=[float(v) for v in values if v is not None]
    if len(vals)!=3: return None
    avg=sum(vals)/3
    return None if avg==0 else max(abs(v-avg) for v in vals)/avg*100
