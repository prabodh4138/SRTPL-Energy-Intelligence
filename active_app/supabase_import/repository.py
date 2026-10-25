class ImportRepository:
    """
    Thin persistence layer. SQL/business rules remain outside Streamlit UI.
    """

    def __init__(self, supabase):
        self.db = supabase

    def file_hash_exists(self, sha256_hash: str) -> bool:
        result = (
            self.db.schema("energy_import")
            .table("import_file")
            .select("import_file_id")
            .eq("sha256_hash", sha256_hash)
            .limit(1)
            .execute()
        )
        return bool(result.data)

    def create_batch(self, payload: dict):
        return (
            self.db.schema("energy_import")
            .table("import_batch")
            .insert(payload)
            .execute()
        ).data[0]

    def create_file(self, payload: dict):
        return (
            self.db.schema("energy_import")
            .table("import_file")
            .insert(payload)
            .execute()
        ).data[0]

    def create_rows(self, rows: list[dict]):
        if not rows:
            return []
        return (
            self.db.schema("energy_import")
            .table("import_row")
            .insert(rows)
            .execute()
        ).data

    def insert_raw(self, schema: str, table: str, rows: list[dict]):
        if not rows:
            return []
        return (
            self.db.schema(schema)
            .table(table)
            .insert(rows)
            .execute()
        ).data

    def update_batch(self, batch_id: str, payload: dict):
        return (
            self.db.schema("energy_import")
            .table("import_batch")
            .update(payload)
            .eq("import_batch_id", batch_id)
            .execute()
        ).data
