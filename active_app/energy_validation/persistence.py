from __future__ import annotations
from typing import Any
from .normalizer import NormalizationEngine
TABLES={"SOLAR":("juno_solar","solar"),"DG":("juno_dg","dg"),"EB":("juno_eb","eb"),"TRANSFORMER":("juno_transformer","transformer"),"UPS":("juno_ups","ups")}
def _clean(row): return {k:v for k,v in row.items() if v is not None}
class NormalizationPersistence:
    def __init__(self,supabase,calculation_version="3.2.1"):
        self.db=supabase; self.calculation_version=calculation_version; self.engine=NormalizationEngine()
    def _batch_rows(self,batch_id):
        files=self.db.schema("energy_import").table("import_file").select("import_file_id").eq("import_batch_id",batch_id).execute().data
        ids=[x["import_file_id"] for x in files]
        if not ids:return []
        return self.db.schema("energy_import").table("import_row").select("import_row_id,import_file_id,source_row_number,raw_payload").in_("import_file_id",ids).order("source_row_number").execute().data
    def _raw_rows(self,report_type,ids):
        table,_=TABLES[report_type]
        if not ids:return []
        return self.db.schema("energy_raw").table(table).select("*").in_("import_row_id",ids).execute().data
    def _asset_id(self,report_type,raw):
        key={"EB":"meter_id","DG":"dg_id","SOLAR":"solar_plant_id","TRANSFORMER":"transformer_id","UPS":"ups_id"}[report_type]
        code=raw.get(key)
        if not code:return None
        data=self.db.schema("energy_master").table("asset").select("asset_id").eq("asset_code",code).limit(1).execute().data
        return data[0]["asset_id"] if data else None
    def _normalized_row(self,t,raw,n):
        base={"asset_id":self._asset_id(t,raw),"import_row_id":raw["import_row_id"],"reading_datetime":raw.get("reading_datetime"),"anomaly_flag":bool(n.get("anomaly_flag")),"data_quality_status":n.get("data_quality_status","VALID")}
        if t=="EB":
            source_mode = (raw.get("source_payload") or {}).get("__source_mode")
            if source_mode == "INTERVAL_CONSUMPTION":
                base.update({
                    "cumulative_kwh": None, "interval_kwh": n.get("interval_kwh"),
                    "cumulative_kvah": None, "interval_kvah": n.get("interval_kvah"),
                    "cumulative_kvarh": None, "interval_kvarh": n.get("interval_kvarh"),
                    "md": raw.get("md"), "pf": raw.get("pf"),
                    "calculation_version": self.calculation_version
                })
            else:
                base.update({
                    "cumulative_kwh":raw.get("kwh"),"interval_kwh":n.get("interval_kwh"),
                    "cumulative_kvah":raw.get("kvah"),"interval_kvah":n.get("interval_kvah"),
                    "cumulative_kvarh":raw.get("kvarh"),"interval_kvarh":n.get("interval_kvarh"),
                    "md":raw.get("md"),"pf":raw.get("pf"),"calculation_version":self.calculation_version
                })
        elif t=="SOLAR": base.update({"cumulative_kwh":raw.get("cumulative_kwh"),"interval_kwh":n.get("interval_kwh"),"calculation_version":self.calculation_version})
        elif t=="DG":
            for k in ("status","kva","kw","voltage_ry","voltage_yb","voltage_br","current_r","current_y","current_b","pf","diesel_level","diesel_topup","load_percent","cumulative_kwh","cumulative_running_hours","rpm"): base[k]=raw.get(k)
            base.update({"interval_kwh":n.get("interval_kwh"),"interval_running_hours":n.get("interval_running_hours"),"calculation_version":self.calculation_version})
        elif t=="TRANSFORMER":
            for k in ("primary_v_ry","primary_v_yb","primary_v_br","primary_i_r","primary_i_y","primary_i_b","secondary_v_ry","secondary_v_yb","secondary_v_br","secondary_i_r","secondary_i_y","secondary_i_b","kwh","kvah","pf","frequency","wti","oti"): base[k]=raw.get(k)
        elif t=="UPS":
            for k in ("main_input_v_r","main_input_v_y","main_input_v_b","main_input_i_r","main_input_i_y","main_input_i_b","rectifier_voltage","bypass_voltage","bypass_current","bypass_frequency","output_voltage","output_current","output_frequency","battery_temperature","battery_vdc","battery_ib"): base[k]=raw.get(k)
        return _clean(base)
    def process_batch(self,batch_id,report_type):
        t=report_type.upper()
        if t not in TABLES: raise ValueError(f"Unsupported report type: {t}")
        batch_rows=self._batch_rows(batch_id)
        row_to_file={r["import_row_id"]: r["import_file_id"] for r in batch_rows}
        raws=self._raw_rows(t,[r["import_row_id"] for r in batch_rows])
        raws.sort(key=lambda r:(row_to_file.get(r["import_row_id"],""),r.get("reading_datetime") or "",r["import_row_id"]))
        previous={}; normalized=[]; exceptions=[]; valid=0
        for raw in raws:
            asset_id=self._asset_id(t,raw)
            # When JUNO metadata does not provide an asset code, use the import
            # file as the sequence boundary. A JUNO file represents one report
            # context, so this preserves cumulative deltas without mixing assets.
            asset_key=str(asset_id) if asset_id else f"file:{row_to_file.get(raw['import_row_id'], raw['import_row_id'])}"
            n,issues=self.engine.process(t,dict(raw),previous.get(asset_key,{})); normalized.append(self._normalized_row(t,raw,n)); previous[asset_key]=dict(raw)
            if issues:
                for issue in issues: exceptions.append(_clean({"import_batch_id":batch_id,"import_row_id":raw["import_row_id"],"asset_id":self._asset_id(t,raw),"exception_code":issue.rule_code,"severity":issue.severity,"status":"OPEN","message":issue.message,"source_value":issue.source_value,"expected_value":issue.expected_value,"metadata":issue.metadata or {}}))
            else: valid+=1
        _,table=TABLES[t]
        if normalized:self.db.schema("energy_readings").table(table).upsert(normalized,on_conflict="import_row_id").execute()
        if exceptions:self.db.schema("energy_validation").table("exception_master").insert(exceptions).execute()
        self.db.schema("energy_import").table("import_batch").update({"status":"IMPORTED","total_rows":len(raws),"valid_rows":valid,"invalid_rows":len(raws)-valid}).eq("import_batch_id",batch_id).execute()
        return {"batch_id":batch_id,"report_type":t,"raw_rows":len(raws),"normalized_rows":len(normalized),"valid_rows":valid,"exception_rows":len(raws)-valid,"calculation_version":self.calculation_version}
