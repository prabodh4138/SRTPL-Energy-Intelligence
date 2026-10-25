# SRTPL Power Consumption Analytics — Master Local Test Baseline

## Purpose
Single project folder for VS Code terminal based local development and Supabase-backed testing.

## Operating rules
1. VS Code terminal is the development/test terminal.
2. One project folder contains the application, SQL, tests, scripts, and source CSV baseline.
3. `.env` is never included. Copy the working `.env` into the project root locally.
4. Original JUNO CSVs under `source_data/raw/` are preserved untouched.
5. CSV structure may change over time. Import detection/parsing must remain metadata/header driven; never depend on fixed row numbers when the source provides identifying labels.
6. NULL is different from zero.
7. Invalid records are retained and traced; they are not silently deleted.
8. Every module must pass local tests first, then real Supabase tests, then application upload tests before the next module starts.
9. Every completed milestone is delivered as a new ZIP.
10. No billing, AI, predictive, or management analytics work should begin until all five source modules are ingestible and KPI-calculable.

## Current module status
- EB: Validated end-to-end (Phase 5.4); browser upload page `eb_juno_import.py`; 100% verified.
- DG: Validated end-to-end (Phase 5.3.1); browser upload page `dg_juno_import.py`; 100% verified.
- Solar: Validated end-to-end (Phase 5.5); browser upload page `solar_juno_import.py`; 100% verified.
- Transformer: Validated end-to-end (Phase 5.6); browser upload page `transformer_juno_import.py`; duplicate detection active; loss/efficiency auditable guard active; 100% verified.
- UPS: Validated end-to-end (Phase 5.7); browser upload page `ups_juno_import.py`; 100% verified.
- Unified Hub: `juno_import_center.py` connects all 5 sources dynamically with auto-detection.

## Source data
All currently supplied CSV files are stored under `source_data/raw/<module>/`.
The application must also support user-uploaded CSVs that are newer/different from these files.

## Local Supabase
Use the existing Supabase project/database and working credentials. Do not commit `.env`.

## DG first test
Use `scripts/verify_dg_phase5_3.py` for local verification. Then use the real DG JUNO upload flow and `scripts/calculate_dg_phase5_3.py` for live Supabase processing.

## Verification commands across all 5 source modules

From VS Code PowerShell terminal:
```powershell
# 1. Run full test suite (73 tests covering all modules & application upload)
.\.venv\Scripts\python.exe -m pytest -q

# 2. Verify all 5 application UI wirings
.\.venv\Scripts\python.exe scripts\verify_eb_app_wiring.py
.\.venv\Scripts\python.exe scripts\verify_dg_app_wiring.py
.\.venv\Scripts\python.exe scripts\verify_solar_app_wiring.py
.\.venv\Scripts\python.exe scripts\verify_transformer_app_wiring.py
.\.venv\Scripts\python.exe scripts\verify_ups_app_wiring.py

# 3. Verify all 5 local normalization & KPI calculations
.\.venv\Scripts\python.exe scripts\verify_eb_phase5_4.py
.\.venv\Scripts\python.exe scripts\verify_dg_phase5_3.py
.\.venv\Scripts\python.exe scripts\verify_solar_phase5_5.py
.\.venv\Scripts\python.exe scripts\verify_transformer_phase5_6.py
.\.venv\Scripts\python.exe scripts\verify_ups_phase5_7.py

# 4. Launch browser application
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```
