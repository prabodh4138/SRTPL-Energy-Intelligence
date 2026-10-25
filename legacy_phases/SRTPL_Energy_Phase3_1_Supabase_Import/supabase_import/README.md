# Phase 3.1 — Supabase Import Integration

This package is the database boundary for the JUNO importer.

## Critical point

The pipeline is deliberately separated:

Parser
  -> ImportPipeline
      -> StorageService
      -> ImportRepository
      -> Raw Mapper

This allows the same parser to be tested without Supabase.

## Current duplicate controls

1. File SHA-256.
2. Source record hash.
3. Business key.
4. Database UNIQUE constraints.

## Production hardening still required

Before production deployment, add:
- PostgreSQL RPC/function for an atomic import transaction.
- Per-record validation transaction.
- Meter reset/replacement handling.
- Asset resolution.
- Normalized reading generation.
- KPI calculation.
- RLS policies appropriate to the application.
- Retry/rollback strategy for Storage vs database failure.
- Import progress/status UI.
