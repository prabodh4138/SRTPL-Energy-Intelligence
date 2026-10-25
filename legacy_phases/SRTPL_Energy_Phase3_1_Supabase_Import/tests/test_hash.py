from supabase_import.hash_utils import sha256_file

def test_sha256(tmp_path):
    p = tmp_path / "test.csv"
    p.write_text("Date,kWh\n01-Apr-2026,10\n", encoding="utf-8")
    assert len(sha256_file(p)) == 64
