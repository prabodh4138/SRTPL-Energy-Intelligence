# Phase Integration Guide

## Phase 3
JUNO parser/detector provides report type, metadata and raw payload.

## Phase 3.1
Import pipeline must be connected to `pages/import_juno.py`:
CSV -> SHA-256 -> duplicate check -> Storage -> import_batch -> import_file -> import_row -> raw table.

## Phase 3.2
Validation/normalization consumes raw records and creates validated normalized readings.

## Phase 3.3
KPI engine consumes normalized readings and stores KPI results.

## Phase 3.4
The Streamlit UI consumes the database/KPI results and provides the browser interface.

## Final assembly
The phase ZIPs are not intended to be independently deployed. They will be merged into one master repository with one requirements file, one environment configuration, one migration sequence and one deployment configuration.
