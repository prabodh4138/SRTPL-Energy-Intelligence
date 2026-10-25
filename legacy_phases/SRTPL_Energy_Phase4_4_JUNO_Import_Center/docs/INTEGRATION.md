# Phase 4.4 Integration

Connect the UI to existing phases:

### Phase 3
Use report detector/parser and multi-row-header parser.

### Phase 3.1
Use ImportPipeline:
CSV → SHA-256 → duplicate check → Storage → import_batch → import_file → import_row → raw tables.

### Phase 3.2
Run validation and normalization after raw import.

### Phase 3.3
Run KPI calculations after normalized readings are committed.

### Supabase Storage
Bucket should be private, e.g. `energy-original-files`.

### Final traceability
import_batch
→ import_file
→ import_row
→ raw JUNO record
→ normalized reading
→ KPI result
→ dashboard.

Do not expose service-role credentials to the browser.
