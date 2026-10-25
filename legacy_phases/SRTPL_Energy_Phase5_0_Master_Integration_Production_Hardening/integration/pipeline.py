from dataclasses import dataclass
from typing import Optional

from .contracts import PIPELINE_STAGES, source_supported

@dataclass
class PipelineContext:
    batch_id: Optional[str] = None
    source_type: Optional[str] = None
    filename: Optional[str] = None
    file_hash: Optional[str] = None
    stage: str = "RECEIVED"
    rows_received: int = 0
    rows_imported: int = 0
    rows_invalid: int = 0
    rows_duplicate: int = 0
    error_message: Optional[str] = None

class MasterPipeline:
    """Orchestration contract.

    Production adapters should be injected for:
    - Phase 3 parser
    - Phase 3.1 Supabase import
    - Phase 3.2 validation/normalization
    - Phase 3.3 KPI engine
    - audit/report services

    The orchestrator owns ordering and failure boundaries, not source-specific
    business rules.
    """

    def validate_source(self, source_type):
        if not source_supported(source_type):
            raise ValueError(f"Unsupported source type: {source_type}")

    def transition(self, ctx, stage):
        if stage not in PIPELINE_STAGES:
            raise ValueError(f"Invalid pipeline stage: {stage}")
        ctx.stage = stage
        return ctx

    def run(self, ctx, adapters):
        self.validate_source(ctx.source_type)

        stages = [
            ("raw_import", "RAW_IMPORTED"),
            ("validation_normalization", "NORMALIZED"),
            ("kpi", "KPI_PROCESSED"),
        ]

        try:
            for adapter_name, stage in stages:
                adapter = adapters.get(adapter_name)
                if adapter is None:
                    raise RuntimeError(f"Missing production adapter: {adapter_name}")
                adapter(ctx)
                self.transition(ctx, stage)

            self.transition(ctx, "COMPLETED")
            return ctx

        except Exception as exc:
            ctx.stage = "FAILED"
            ctx.error_message = str(exc)
            raise
