# SRTPL Energy Intelligence

SRTPL Energy Intelligence runs on Render as a React/Vite web app and a FastAPI backend, with Supabase PostgreSQL as its data store. Render configuration is in render.yaml.

## Deploy on Render

1. Push this repository's main branch to GitHub.
2. In Render, create a Blueprint from this repository and apply render.yaml.
3. Set SUPABASE_URL, SUPABASE_KEY, and SUPABASE_SERVICE_ROLE_KEY for the backend service.
4. Confirm the frontend service's VITE_API_URL points to the backend's public Render URL.

The backend starts with uvicorn backend.main:app; the frontend is built from frontend/ and served as a static site.

## Module 7 Analytics

Module 7 uses the React Analytics page and the FastAPI route at /api/energy/analytics/module/{module_name}. It reads the additive SQL views for DG, EB, Solar, Transformer, and UPS, along with the shared Module 7 views.

The proposed view package, deployment order, and read-only preflight are in sql/module7_analytics_proposed/. Deploy the five submodule view files before the unified views. The correction-audit view is optional. If required SQL views are not available, the Analytics page reports that state instead of substituting fabricated KPI values.

Approved monitoring rules include universal Total Records = VALID + EXCEPTION, entry delay of at least 24 hours, and independent night indicators from 22:00 inclusive to 06:00 exclusive in Asia/Kolkata. DG cumulative runtime is interpreted as HH.MM and presented as HH:MM.

## Project status

The repository contains legacy modules and local source data alongside the Render application. Production readiness still depends on confirming the target Supabase schema, deploying the Module 7 SQL views, configuring Render secrets, and completing deployment validation.
