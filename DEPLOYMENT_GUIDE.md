# SRTPL Power Consumption Analytics — Deployment & Multi-Device Access Guide

This guide details how to run the application locally on your PC, access it seamlessly from any mobile phone or secondary laptop, deploy to cloud hosting with a permanent global link, inject sample data into Supabase, and wipe all operational data for a clean production start.

---

## 1. Local PC & Mobile / Laptop Access (Wi-Fi / LAN)

### Step 1: Start the Application on your Host PC
Run the following command in terminal:
```bash
streamlit run streamlit_app.py
```
Streamlit starts and automatically binds to all network interfaces (`0.0.0.0:8501`) as defined in `.streamlit/config.toml`.

### Step 2: Open on Your Local PC
- **URL**: [http://localhost:8501](http://localhost:8501)

### Step 3: Open on Any Mobile Phone or Secondary Laptop
Make sure your smartphone, tablet, or secondary laptop is connected to the **same Wi-Fi / Local Area Network** as the host PC.

- **Network URL**: `http://<YOUR_PC_IP>:8501`
- **Current Host Network URL**: **`http://10.157.111.68:8501`**

> **Tip:** You can check your machine's live Network URL at any time by running:
> ```bash
> python scripts/supabase_manager.py --network
> ```
> Or by looking at the sidebar inside the application under **📱 MOBILE / LAPTOP ACCESS**.

#### Windows Firewall Note (If phone cannot reach the PC):
If your mobile device times out when loading `http://10.157.111.68:8501`, allow port 8501 through Windows Defender Firewall:
1. Open PowerShell as Administrator.
2. Run:
   ```powershell
   New-NetFirewallRule -DisplayName "Streamlit Port 8501" -Direction Inbound -LocalPort 8501 -Protocol TCP -Action Allow
   ```

---

## 2. Cloud Deployment (Global Public Access via Phone / Laptop Anywhere)

To access the platform anywhere in the world on cellular 4G/5G or external networks without being on the same local Wi-Fi, deploy it to **Streamlit Community Cloud** (100% Free):

### Option A: Streamlit Community Cloud (Recommended & Instant)
1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Deploy SRTPL Energy Intelligence"
   git push origin main
   ```
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and log in with your GitHub account.
3. Click **"New App"** (or "Create app").
4. Fill in the repository details:
   - **Repository**: `YourGitHubUsername/srtpl-power-project`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
5. Click **"Advanced settings..."** -> **Secrets** and paste your Supabase keys:
   ```toml
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_KEY = "your-service-role-or-anon-key"
   ```
6. Click **Deploy!**
7. In ~60 seconds, you will receive a public HTTPS URL (e.g. `https://srtpl-energy.streamlit.app`). This link works instantly on **any iPhone, Android smartphone, Mac, or PC** worldwide.

### Option B: Containerized Cloud Deployment (Docker / Render / Cloud Run)
A production-ready `Dockerfile` and `.dockerignore` are included in the repository.
To build and run with Docker:
```bash
docker build -t srtpl-energy:latest .
docker run -p 8501:8501 --env-file .env srtpl-energy:latest
```

---

## 3. Supabase Database Integration & Data Injection

### Step 1: Create a Free Supabase Project
1. Go to [supabase.com](https://supabase.com) and create a free project.
2. Note your **Project URL** and **API Keys** (`anon` and `service_role`).

### Step 2: Create Database Tables in Supabase
1. Open your Supabase Dashboard -> **SQL Editor**.
2. Click **New Query**, copy the contents of `sql/supabase_master_setup.sql`, paste it, and click **Run**.
3. All required tables, foreign keys, indexes, and convenience views are created instantly.

### Step 3: Inject Data into Supabase
You can inject the full suite of data (3 Toll Plazas, 21 Assets, raw JUNO meter readings, 13 verified Energy Bills, and 4 Payment Receipts) either via the Web UI or via the CLI:

- **Via Web UI**:
  1. Open the application.
  2. Navigate to **Administration** -> tab **"Database & Cloud Deployment"**.
  3. Under **📥 Inject Data into Database**, click **"🚀 Inject Data into Database / Supabase"**.
  4. Live progress is displayed, and record counts are confirmed upon completion.

- **Via CLI**:
  ```bash
  python scripts/supabase_manager.py --inject
  ```

---

## 4. Remove All Data from Database (Clean Production Reset)

When you are ready to transition from testing to live production, you can completely wipe all sample and test data:

- **Via Web UI**:
  1. Navigate to **Administration** -> tab **"Database & Cloud Deployment"**.
  2. Check the safety box: **"I confirm I want to wipe all operational data from the database"**.
  3. Click **"⚠️ Wipe Database / Remove All Data"**.
  4. All telemetry logs, raw CSV caches, bills, and receipts are deleted immediately, leaving a pristine empty database ready for real uploads.

- **Via CLI**:
  ```bash
  python scripts/supabase_manager.py --reset
  ```

- **Via Supabase SQL Editor**:
  Run `sql/reset_database.sql` directly in Supabase to truncate all operational tables with CASCADE.

---

## 5. Verification Commands
To verify the complete setup locally at any time:
```bash
# Check database status and access links
python scripts/supabase_manager.py --status --network

# Run the full test suite
python -m pytest active_app/tests/ -q
```
