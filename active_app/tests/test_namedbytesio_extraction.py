import io
import pytest
from bill_extractor.zip_handler import NamedBytesIO, extract_pdfs_from_inputs


def test_named_bytes_io_get_and_indexing():
    sample_bytes = b"%PDF-1.4 test data"
    obj = NamedBytesIO(sample_bytes, name="EB_test_123.pdf")

    # Attribute access
    assert obj.name == "EB_test_123.pdf"
    assert obj.getvalue() == sample_bytes

    # Dict-like .get() access
    assert obj.get("name") == "EB_test_123.pdf"
    assert obj.get("filename") == "EB_test_123.pdf"
    assert obj.get("bytes") == sample_bytes
    assert obj.get("content") == sample_bytes
    assert obj.get("non_existent", "default_val") == "default_val"

    # Dict-like [] indexing
    assert obj["name"] == "EB_test_123.pdf"
    assert obj["filename"] == "EB_test_123.pdf"
    assert obj["bytes"] == sample_bytes


def test_unpacked_items_handling_safe():
    sample_bytes = b"%PDF-1.4 mock content"
    obj = NamedBytesIO(sample_bytes, name="mock_bill.pdf")

    unpacked_items = [obj]
    for idx, item in enumerate(unpacked_items):
        if isinstance(item, dict):
            fname = item.get("filename") or item.get("name") or f"file_{idx}.pdf"
            raw_bytes = item.get("bytes") or item.get("content") or b""
        else:
            fname = getattr(item, "name", None) or f"file_{idx}.pdf"
            if hasattr(item, "getvalue"):
                raw_bytes = item.getvalue()
            elif hasattr(item, "read"):
                item.seek(0)
                raw_bytes = item.read()
            else:
                raw_bytes = bytes(item) if item else b""

        assert fname == "mock_bill.pdf"
        assert raw_bytes == sample_bytes
