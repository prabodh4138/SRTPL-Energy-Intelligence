# Deployment

## Development
Run locally on the personal development laptop only.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Production
The final application is deployed as a web service. Office users do not install Python or an EXE.

Configure:
- SUPABASE_URL
- SUPABASE_KEY
- ADMIN_EMAIL
- ADMIN_TOKEN

Before production:
1. Apply all database migrations.
2. Configure Supabase Storage private bucket.
3. Configure RLS.
4. Integrate Phase 3.1 import pipeline.
5. Integrate Phase 3.2 validation/normalization.
6. Integrate Phase 3.3 KPI engine.
7. Test real JUNO files.
8. Verify audit traceability.
9. Perform mobile/office-browser UAT.
10. Only then switch to production.
