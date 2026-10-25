import pytest
from integration.contracts import source_supported, PIPELINE_STAGES
from integration.idempotency import import_identity, duplicate_blocked
from integration.pipeline import MasterPipeline, PipelineContext

def test_supported_sources():
    assert source_supported("SOLAR")
    assert source_supported("DG")
    assert not source_supported("TPWODL_BILL")

def test_import_identity():
    assert import_identity("abc", "SOLAR") == "SOLAR:abc"

def test_duplicate():
    assert duplicate_blocked("abc", "abc")
    assert not duplicate_blocked("abc", "xyz")

def test_missing_adapter_fails():
    ctx = PipelineContext(source_type="SOLAR")
    with pytest.raises(RuntimeError):
        MasterPipeline().run(ctx, {})
    assert ctx.stage == "FAILED"

def test_stages_exist():
    assert "COMPLETED" in PIPELINE_STAGES
