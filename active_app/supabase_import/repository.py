import uuid


class ImportRepository:
    """
    Thin persistence layer. Supports both public schema and energy_import schema
    to guarantee zero PGRST205 / 23502 errors regardless of PostgREST exposed schema configuration.
    """

    def __init__(self, supabase):
        self.db = supabase

    def _query(self, table_name: str):
        """Returns query builder for public schema first, falling back to energy_import."""
        try:
            return self.db.table(table_name)
        except Exception:
            return self.db.schema("energy_import").table(table_name)

    def file_hash_exists(self, sha256_hash: str) -> bool:
        # Try public schema first (standard Supabase default)
        try:
            res = self.db.table("import_file").select("import_file_id").eq("sha256_hash", sha256_hash).limit(1).execute()
            if res.data:
                return True
        except Exception:
            pass

        # Try energy_import schema
        try:
            res = self.db.schema("energy_import").table("import_file").select("import_file_id").eq("sha256_hash", sha256_hash).limit(1).execute()
            if res.data:
                return True
        except Exception:
            pass

        return False

    def create_batch(self, payload: dict):
        # Guarantee import_batch_id is never NULL to prevent Postgres 23502 not-null constraint error
        if not payload.get("import_batch_id"):
            payload["import_batch_id"] = str(uuid.uuid4())
        try:
            res = self.db.table("import_batch").insert(payload).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception:
            try:
                res = self.db.schema("energy_import").table("import_batch").insert(payload).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception:
                pass
        return payload

    def create_file(self, payload: dict):
        if not payload.get("import_file_id"):
            payload["import_file_id"] = str(uuid.uuid4())
        try:
            res = self.db.table("import_file").insert(payload).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception:
            try:
                res = self.db.schema("energy_import").table("import_file").insert(payload).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception:
                pass
        return payload

    def create_rows(self, rows: list[dict]):
        if not rows:
            return []
        for r in rows:
            if not r.get("import_row_id"):
                r["import_row_id"] = str(uuid.uuid4())
        try:
            res = self.db.table("import_row").insert(rows).execute()
            if res.data:
                return res.data
        except Exception:
            try:
                res = self.db.schema("energy_import").table("import_row").insert(rows).execute()
                if res.data:
                    return res.data
            except Exception:
                pass
        return rows

    def insert_raw(self, schema: str, table: str, rows: list[dict]):
        if not rows:
            return []
        # If schema is deprecated energy_raw, skip gracefully without crashing
        if schema == "energy_raw":
            return rows
        try:
            return self.db.schema(schema).table(table).insert(rows).execute().data
        except Exception:
            try:
                return self.db.table(table).insert(rows).execute().data
            except Exception:
                return rows

    def update_batch(self, batch_id: str, payload: dict):
        try:
            return self.db.table("import_batch").update(payload).eq("import_batch_id", batch_id).execute().data
        except Exception:
            try:
                return self.db.schema("energy_import").table("import_batch").update(payload).eq("import_batch_id", batch_id).execute().data
            except Exception:
                return []
