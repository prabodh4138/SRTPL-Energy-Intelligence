# SRTPL Power Analytics — EB First Test Gate

**Current active module: EB only.**

Project root requested by the user:

`C:\Users\prabo\OneDrive\Desktop\srtpl power project`

Do not create a separate project root. Extract this ZIP into that single folder.

## Gate rule

Do not start DG, Solar, Transformer or UPS until EB passes:

1. Local parser/validation/KPI test
2. Real Supabase import + normalization + validation + KPI test
3. Actual Streamlit browser CSV upload test

## EB source formats supported

The package recognizes the supplied EB source formats without editing the original CSV:

- `SRTPL_Test_JUNO_EB.csv` — controlled cumulative test
- `EBDailyLogReport_25thSep2026_2143_EB Log - Copy.csv` — JUNO EB log
- `EB_Daily_Consumption_25thSep2026_6841_EB Daily.csv` — detailed daily consumption

The detailed daily format is treated as interval consumption; it is **not** incorrectly differenced as a cumulative meter.

## Local test

From VS Code terminal:

```powershell
cd "C:\Users\prabo\OneDrive\Desktop\srtpl power project"
.\.venv\Scripts\python.exe scripts\verify_eb_phase5_4.py
.\.venv\Scripts\python.exe scripts\verify_eb_app_wiring.py
.\.venv\Scripts\python.exe -m pytest -q
```

Expected controlled EB result:

- Parsed rows: 7
- Valid rows: 5
- Exception rows: 2
- Validated consumption: 125.0 kWh
- Validated KVAH: 125.0 kVAH
- Validated KVARH: 47.0 kVARH
- Six validation rule hits across the two exception readings: VAL-EB-001, VAL-EB-002 and VAL-EB-004

## Supabase / browser test

Copy your existing `.env` into the project root. Do not put credentials into the ZIP.

Then:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Login and open:

**EB JUNO Import**

Upload:

`source_data\raw\EB\SRTPL_Test_JUNO_EB.csv`

Click:

**Import EB → Supabase → Validate → Calculate KPI**

Verify the displayed batch, import file, validation summary, KPI values and source reading IDs.

The application must preserve the exact uploaded CSV in the private `energy-original-files` bucket.

## Next step

Only after the user confirms the EB browser/Supabase test is successful should the project move to DG.
