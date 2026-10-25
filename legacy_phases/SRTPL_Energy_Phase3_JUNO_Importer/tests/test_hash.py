from import_engine.hash_utils import sha256_file

def test_hash(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("abc", encoding="utf-8")
    assert len(sha256_file(p)) == 64
