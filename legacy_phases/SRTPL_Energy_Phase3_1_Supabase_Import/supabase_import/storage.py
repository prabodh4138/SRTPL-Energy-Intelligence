from pathlib import Path

class StorageService:
    def __init__(self, supabase, bucket: str):
        self.supabase = supabase
        self.bucket = bucket

    def upload_original(self, file_path: str, storage_path: str):
        """
        Uploads the exact original file. No parsing, rewriting or CSV
        normalization occurs before this operation.
        """
        path = Path(file_path)
        with open(path, "rb") as f:
            data = f.read()

        return self.supabase.storage.from_(self.bucket).upload(
            storage_path,
            data,
            {"content-type": "text/csv", "upsert": "false"},
        )
