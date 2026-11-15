# Deployment Guide

The supported hosted application uses Render with a React/Vite static frontend, a FastAPI web service, and Supabase PostgreSQL. The Render Blueprint is defined in render.yaml; detailed setup steps are in CLOUD_DEPLOYMENT_GUIDE.md.

## Render services

- Backend: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
- Frontend: build from frontend/ with npm run build, publish frontend/dist
- Database: Supabase project with the required schemas and Module 7 SQL views

Configure SUPABASE_URL, SUPABASE_KEY, and SUPABASE_SERVICE_ROLE_KEY in the Render backend service. Keep secrets in Render's environment settings; do not commit them.

## Module 7 SQL setup

Use the package in sql/module7_analytics_proposed/. Run Module_7_ReadOnly_Preflight.sql first. After confirming source columns and view names, deploy the five submodule view files and then Module_7_Unified_Views_Proposed.sql. The correction-audit view is optional and guarded for a missing audit source.

The Module 7 frontend reads only these SQL views. If the views are not deployed or accessible, the page shows the required view names and deployment guidance.

## Local development

Start the backend with:

    uvicorn backend.main:app --reload --port 8000

Start the React frontend from frontend/ with:

    npm run dev

Set VITE_API_URL to the backend base URL when it differs from the default local endpoint.
