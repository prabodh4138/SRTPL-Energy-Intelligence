# 🚀 SRTPL Energy Intelligence — Cloud Deployment Guide

This guide details the complete, step-by-step production deployment for the **SRTPL Energy Intelligence System** using:
1. **Database & Storage**: [Supabase Cloud](https://supabase.com) (PostgreSQL)
2. **Backend API**: [Render](https://render.com) or [Railway](https://railway.app) (FastAPI Python)
3. **Frontend Application**: [Vercel](https://vercel.com) or [Netlify](https://netlify.com) (React 19 + Vite)

---

## Architecture Topology

```
                  ┌──────────────────────────────┐
                  │    React Frontend (Vercel)   │
                  │   https://srtpl-energy.app   │
                  └──────────────┬───────────────┘
                                 │
                    HTTPS Requests (API Calls)
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │   FastAPI Backend (Render)   │
                  │  https://api.srtpl-energy.com│
                  └──────────────┬───────────────┘
                                 │
                   PostgreSQL / Storage / Auth
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │        Supabase Cloud        │
                  │  • energy_master schema      │
                  │  • public schema & SQL views │
                  │  • PDF Storage Buckets       │
                  └──────────────────────────────┘
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
     - Bucket 1: `energy-bills` (Public or Private with RLS)
     - Bucket 2: `payment-receipts`
5. **Verify Database Schemas**:
   - Open **SQL Editor** in Supabase and ensure schemas `energy_master` and `public` are ready:
     ```sql
     CREATE SCHEMA IF NOT EXISTS energy_master;
     CREATE SCHEMA IF NOT EXISTS public;
     ```

---

## Step 2: Deploy FastAPI Backend (Render or Railway)

### Option A: Render (Recommended — 1-Click Blueprint)

The repository includes a ready-to-use [`render.yaml`](render.yaml) file.

1. Go to [https://render.com](https://render.com) and connect your GitHub repository (`SRTPL-Energy-Intelligence`).
2. Click **New +** → **Blueprint**.
3. Select your repository. Render automatically reads `render.yaml` and sets up:
   - **`srtpl-energy-backend`** (FastAPI Web Service)
   - **`srtpl-energy-frontend`** (React Static Site)
4. Add the required Environment Variables in Render:
   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `SUPABASE_URL` | `https://<your-project-id>.supabase.co` | Your Supabase Project URL |
   | `SUPABASE_KEY` | `eyJh...` (Service Role or Anon) | Backend API key |
   | `DATABASE_URL` | `postgresql://postgres:...` | Direct PostgreSQL connection string |
5. Click **Apply**. Render will build and deploy your backend. Your backend URL will look like:
   `https://srtpl-energy-backend.onrender.com`

---

### Option B: Railway (Docker Deployment)

The repository includes [`Dockerfile.backend`](Dockerfile.backend) and [`railway.json`](railway.json).

1. Go to [https://railway.app](https://railway.app).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select `SRTPL-Energy-Intelligence`.
4. Under **Variables**, add:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `PORT=8000`
5. Railway will automatically build using `Dockerfile.backend` and provide a public URL like:
   `https://srtpl-energy-intelligence-production.up.railway.app`

---

## Step 3: Deploy React Frontend (Vercel or Netlify)

### Option A: Vercel (Fastest & Free)

1. Go to [https://vercel.com](https://vercel.com) and log in with GitHub.
2. Click **Add New** → **Project**.
3. Import `SRTPL-Energy-Intelligence`.
4. Configure Project Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend` *(Important! Click Edit and select the `frontend` folder)*
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Under **Environment Variables**, add:
   | Key | Value |
   | :--- | :--- |
   | `VITE_API_URL` | `https://srtpl-energy-backend.onrender.com` *(Your deployed FastAPI Backend URL)* |
   | `VITE_SUPABASE_URL` | `https://<your-project-id>.supabase.co` |
   | `VITE_SUPABASE_ANON_KEY` | `eyJh...` *(Your Supabase Anon Key)* |
6. Click **Deploy**. Vercel will build and deploy in ~30 seconds, generating your live domain (e.g. `https://srtpl-energy-frontend.vercel.app`).

---

### Option B: Netlify

1. Go to [https://netlify.com](https://netlify.com).
2. Click **Add new site** → **Import an existing project**.
3. Select `frontend` as base directory and `dist` as publish directory.
4. Add `VITE_API_URL` under Site Settings → Environment Variables.
5. Click **Deploy Site**.

---

## Step 4: Verification & Smoke Test

Once deployed, verify your live system:

1. **Backend Health Check**:
   - Open: `https://your-backend-url.onrender.com/api/health`
   - Expected JSON:
     ```json
     {
       "status": "ONLINE",
       "service": "SRTPL Energy Intelligence FastAPI",
       "version": "2.0.0",
       "database": "CONNECTED"
     }
     ```
2. **Interactive Swagger Documentation**:
   - Open: `https://your-backend-url.onrender.com/docs`
   - Test endpoints: `/api/dashboard/summary`, `/api/consumers/`, `/api/bills/register`.
3. **React Frontend**:
   - Open: `https://your-frontend-url.vercel.app`
   - Test extraction: Drop sample bill PDF (`411001070208_82025_EN.pdf`).
   - Verify calculation badges (`VERIFIED ✓`), Review Queue holding, and Excel/CSV export.

---

## Quick Reference: Environment Variables

### Backend (`.env` or Cloud Provider Settings)
```ini
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-service-role-or-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
DATABASE_URL=postgresql://postgres:password@db.your-project-id.supabase.co:5432/postgres
PORT=8000
```

### Frontend (`frontend/.env` or Vercel Settings)
```ini
VITE_API_URL=https://your-backend-url.onrender.com
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```
