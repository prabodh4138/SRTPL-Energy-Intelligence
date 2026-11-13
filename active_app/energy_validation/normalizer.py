from .solar import validate_solar
from .dg import validate_dg
from .eb import validate_eb
from .transformer import validate_transformer
from .ups import validate_ups
from .thresholds import ThresholdProvider

class NormalizationEngine:

    def __init__(self, threshold_provider=None):
        self.thresholds = threshold_provider or ThresholdProvider()

    def process(self, report_type, current, previous=None):
        previous = previous or {}

        if report_type == "SOLAR":
            issues, delta, state = validate_solar(current, previous)
            normalized = {
                **current,
                "interval_kwh": delta if state == "NORMAL" else None,
                "data_quality_status": "VALID" if not issues else "EXCEPTION",
                "anomaly_flag": bool(issues),
            }

        elif report_type == "DG":
            issues, derived = validate_dg(
                current,
                previous,
                self.thresholds.thresholds
            )
            normalized = {
                **current,
                "interval_kwh": derived["interval_kwh"] if derived["kwh_state"] == "NORMAL" else None,
                "interval_running_hours":
                    derived["interval_running_hours"]
                    if derived["runtime_state"] == "NORMAL" else None,
                "data_quality_status": "VALID" if not issues else "EXCEPTION",
                "anomaly_flag": bool(issues),
            }

        elif report_type == "EB":
            source_mode = (current.get("source_payload") or {}).get("__source_mode")
            if source_mode == "INTERVAL_CONSUMPTION":
                # Detailed Daily JUNO exports already contain interval
                # consumption. Do not subtract one daily consumption value
                # from the next; that would create a false cumulative delta.
                issues = []
                from .common import check_pf
                pf_issue = check_pf(current.get("pf"), "VAL-EB-003", "EB PF")
                if pf_issue:
                    issues.append(pf_issue)
                normalized = {
                    **current,
                    "interval_kwh": current.get("kwh"),
                    "interval_kvah": current.get("kvah"),
                    "interval_kvarh": current.get("kvarh"),
                    "data_quality_status": "VALID" if not issues else "EXCEPTION",
                    "anomaly_flag": bool(issues),
                }
            else:
                issues, derived = validate_eb(current, previous)
                normalized = {
                    **current,
                    "interval_kwh": derived["interval_kwh"] if derived["kwh_state"] == "NORMAL" else None,
                    "interval_kvah": derived["interval_kvah"] if derived["kvah_state"] == "NORMAL" else None,
                    "interval_kvarh": derived["interval_kvarh"] if derived["kvarh_state"] == "NORMAL" else None,
                    "data_quality_status": "VALID" if not issues else "EXCEPTION",
                    "anomaly_flag": bool(issues),
                }

        elif report_type == "TRANSFORMER":
            issues = validate_transformer(current, self.thresholds.thresholds)

            # Compute interval delta for KWH and KVAH if sequential readings exist
            cur_kwh = None
            prev_kwh = None
            cur_kvah = None
            prev_kvah = None
            try:
                if current.get("kwh") is not None:
                    cur_kwh = float(current["kwh"])
                if previous.get("kwh") is not None:
                    prev_kwh = float(previous["kwh"])
                if current.get("kvah") is not None:
                    cur_kvah = float(current["kvah"])
                if previous.get("kvah") is not None:
                    prev_kvah = float(previous["kvah"])
            except (ValueError, TypeError):
                pass

            interval_kwh = round(cur_kwh - prev_kwh, 4) if (cur_kwh is not None and prev_kwh is not None and cur_kwh >= prev_kwh) else None
            interval_kvah = round(cur_kvah - prev_kvah, 4) if (cur_kvah is not None and prev_kvah is not None and cur_kvah >= prev_kvah) else None

            normalized = {
                **current,
                "interval_kwh": interval_kwh,
                "interval_kvah": interval_kvah,
                "data_quality_status": "VALID" if not issues else "EXCEPTION",
                "anomaly_flag": bool(issues),
            }

        elif report_type == "UPS":
            issues = validate_ups(current, self.thresholds)
            normalized = {
                **current,
                "data_quality_status": "VALID" if not issues else "EXCEPTION",
                "anomaly_flag": bool(issues),
            }

        else:
            raise ValueError(f"Unsupported report type: {report_type}")

        return normalized, issues
