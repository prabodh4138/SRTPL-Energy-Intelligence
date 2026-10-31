# 🚀 SRTPL Energy Intelligence — Cloud Deployment Guide

This guide details the complete, production deployment for the **SRTPL Energy Intelligence System** hosted entirely on **Render** (both Frontend & Backend in one Blueprint) connected to **Supabase Cloud**.

1. **Database & Storage**: [Supabase Cloud](https://supabase.com) (PostgreSQL)
2. **Backend API**: [Render](https://render.com) (`srtpl-energy-backend` — Python FastAPI Web Service)
3. **Frontend Application**: [Render](https://render.com) (`srtpl-energy-frontend` — React 19 Static Site)

*(Vercel is omitted; everything runs inside Render for unified management).*

---

## Architecture Topology

```
                  ┌───────────────────────────────────────────────┐
                  │      React Frontend (Render Static Site)      │
                  │     https://srtpl-energy-frontend.onrender    │
                  └───────────────────────┬───────────────────────┘
                                          │
                            HTTPS Requests (API Calls)
                                          │
                                          ▼
                  ┌───────────────────────────────────────────────┐
                  │      FastAPI Backend (Render Web Service)     │
                  │      https://srtpl-energy-backend.onrender    │
                  └───────────────────────┬───────────────────────┘
                                          │
                            PostgreSQL / Storage / Auth
                                          │
                                          ▼
                  ┌───────────────────────────────────────────────┐
                  │                Supabase Cloud                 │
                  │  • energy_master schema                       │
                  │  • public schema & SQL views                  │
                  │  • PDF Storage Buckets                        │
                  └───────────────────────────────────────────────┘
```

---

## Step 1: Configure Supabase Cloud Database

1. **Log in to Supabase**:
   - Go to [https://supabase.com](https://supabase.com) and create or open your project.
2. **Retrieve API Credentials**:
   - Navigate to **Project Settings** → **API**.
   - Note down:
     - **Project URL**: `https://<your-project-id>.supabase.co`
     - **Anon Key**: `eyJh...` (Public client key)
     - **Service Role Key**: `eyJh...` (Secret backend key for admin queries)
3. **Retrieve Database Connection String**:
   - Navigate to **Project Settings** → **Database** → **Connection String** (URI).
   - Format: `postgresql://postgres:[YOUR-PASSWORD]@db.<your-project-id>.supabase.co:5432/postgres`
4. **Create Supabase Storage Buckets**:
   - In Supabase dashboard, click **Storage** → **New Bucket**:
     - Bucket 1: `energy-bills`
     - Bucket 2: `payment-receipts`
5. **Verify Database Schemas**:
   - Open **SQL Editor** in Supabase and ensure schemas `energy_master` and `public` are ready:
     ```sql
     CREATE SCHEMA IF NOT EXISTS energy_master;
     CREATE SCHEMA IF NOT EXISTS public;
     ```

---

## Step 2: 1-Click Deploy on Render (Frontend + Backend Together)

The repository includes [`render.yaml`](render.yaml) which configures **both** services simultaneously:

1. **Open Render**:
   - Go to [https://dashboard.render.com](https://dashboard.render.com).
2. **Create New Blueprint Instance**:
   - Click **New +** → **Blueprint**.
   - Connect your GitHub repository: `prabodh4138/SRTPL-Energy-Intelligence`.
3. **Render Automatically Configures Both Services**:
   - **Service 1: `srtpl-energy-backend`** (Web Service, Python 3.11, FastAPI)
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Service 2: `srtpl-energy-frontend`** (Static Site, React 19 + Vite)
     - Root Directory: `frontend`
     - Build Command: `npm install && npm run build`
     - Publish Directory: `dist`
4. **Enter Your Supabase Environment Variables**:
   Render will prompt for the variables defined with `sync: false`:
   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `SUPABASE_URL` | `https://<your-project-id>.supabase.co` | Your Supabase Project URL |
   | `SUPABASE_KEY` | `eyJh...` | Your Supabase Service Role Key or Anon Key |
   | `SUPABASE_SERVICE_ROLE_KEY` | `eyJh...` | Your Supabase Service Role Key |
5. **Click "Apply"**:
   - Render starts deploying both services in parallel.
   - Build logs will show Python wheels installing and Vite bundling `dist/`.
6. **Live URLs**:
   - **Backend API**: `https://srtpl-energy-backend.onrender.com`
   - **Swagger / OpenAPI Documentation**: `https://srtpl-energy-backend.onrender.com/docs`
   - **Frontend UI**: `https://srtpl-energy-frontend.onrender.com`

---

## Step 3: Verification & Smoke Test

1. **Verify Backend Health**:
   - Open: `https://srtpl-energy-backend.onrender.com/api/health`
   - Response:
     ```json
     {
       "status": "ONLINE",
       "service": "SRTPL Energy Intelligence FastAPI",
       "version": "2.0.0",
       "database": "ACTIVE"
     }
     ```
2. **Verify Frontend UI**:
   - Open: `https://srtpl-energy-frontend.onrender.com`
   - The top header will display:
     - `FastAPI: ONLINE` (green indicator)
     - `Supabase: ACTIVE` (cyan indicator)
   - Test navigating across all 6 modules:
     - 1. **Dashboard**
     - 2. **Reading Section** (DG, EB, SOLAR, TRANSFORMER, UPS)
     - 3. **Validation and Exceptions**
     - 4. **Juno Import Centre**
     - 5. **Bill Reconciliation & Review Queue**
     - 6. **Reports** (Excel, CSV, PDF)

3. **Dynamic API Configuration (If Needed)**:
   - If your Render backend was assigned an alternative URL suffix, you don't even need to rebuild the frontend:
   - Click the **FastAPI badge** in the frontend header, enter your backend URL, and click **Save & Connect**.
