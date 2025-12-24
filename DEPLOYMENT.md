# 🚀 Ultimate Deployment Guide

This guide will walk you through deploying **B2B Outreach Pro** to the cloud. You have many options, but we recommend **Render + Neon** for the best free/cheap experience.

---

## 🏗️ Prerequisites
1.  **GitHub Account**: You need to upload this code to a GitHub repository.
2.  **Git Installed**: You need `git` on your computer.

### Step 0: Push Code to GitHub
If you haven't already:
```bash
git init
git add .
git commit -m "Initial commit"
# Create a new repo on GitHub.com and follow instructions to push:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

---

## 🗄️ Part 1: Choose a Database (Postgres)
Local `leads.db` (SQLite) is great for testing, but for Cloud, you need **PostgreSQL**.

### Option A: Neon.tech (Recommended - Free & Fast)
1.  Go to [Neon.tech](https://neon.tech) and sign up.
2.  Create a **New Project**.
3.  Copy the **Connection String** (looks like `postgres://user:pass@ep-xyz.neon.tech/neondb`).
    *   *Note: You will use this as your `DATABASE_URL` later.*

### Option B: Supabase (Alternative - Free)
1.  Go to [Supabase.com](https://supabase.com) and sign up.
2.  Create a **New Project**.
3.  Go to **Project Settings -> Database**.
4.  Copy the **Connection String (URI)**. Replace `[YOUR-PASSWORD]` with the one you created.

---

## ☁️ Part 2: Choose a Hosting Platform

### 🥇 Option 1: Render (Easiest)
**Pros**: Native Python support, free tier (spins down on inactivity).
1.  Go to [Render.com](https://render.com).
2.  Click **New +** -> **Web Service**.
3.  Connect your GitHub repository.
4.  **Settings**:
    *   **Runtime**: Python 3
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
5.  **Environment Variables** (Advanced):
    *   Expose key: `DATABASE_URL` -> Value: (Your Neon/Supabase connection string)
    *   Expose key: `AI_API_KEY` -> Value: (Your OpenAI Key)
    *   Expose key: `SMTP_PASSWORD` -> Value: (Your Email Password)
6.  Click **Create Web Service**.

### 🥈 Option 2: Railway (Best Performance)
**Pros**: Fast, keeps running, $5 credit usually handles small usage.
1.  Go to [Railway.app](https://railway.app).
2.  Click **New Project** -> **GitHub Repo**.
3.  Select your repository.
4.  It will verify the `Procfile` and deploy.
5.  **Variables**: 
    *   Go to **Variables** tab.
    *   Add `DATABASE_URL` (Your Postgres URL).
    *   Add `AI_API_KEY`, etc.
6.  Railway usually auto-detects everything.

### 🥉 Option 3: Heroku (Classic)
**Pros**: Very stable, large ecosystem. **Cons**: No longer free ($5/mo minimum).
1.  Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).
2.  Login: `heroku login`
3.  Create app: `heroku create b2b-outreach-app`
4.  Add Database (Optional, internal Heroku Postgres):
    *   `heroku addons:create heroku-postgresql:hobby-dev`
    *   *(Or just set `DATABASE_URL` config var if using Neon)*
5.  Set configs:
    *   `heroku config:set AI_API_KEY=sk-...`
6.  Deploy:
    *   `git push heroku main`

### 🏅 Option 4: Vercel (Serverless)
**Pros**: Great for frontend + API. **Cons**: Serverless Python can be tricky with long-running tasks (background workers might time out).
1.  Install Vercel CLI or go to [Vercel.com](https://vercel.com).
2.  Import your GitHub repo.
3.  Vercel will detect `vercel.json`.
4.  **Environment Variables**:
    *   Add `DATABASE_URL`, `AI_API_KEY` in the Project Settings.
5.  Deploy.
    *   *Warning*: Background tasks (like bulk emailing) might be limited by Vercel's 10-second timeout on the free tier.

---

## 🛠️ Configuration Checklist (Environment Variables)
When deploying, make sure to set these **Environment Variables** in your platform's dashboard:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | Connection to Postgres | `postgres://user:pass@host/db` |
| `AI_PROVIDER` | Which AI to use | `openai` |
| `AI_API_KEY` | Your AI Secret Key | `sk-...` |
| `SMTP_USER` | Email address for sending | `me@company.com` |
| `SMTP_PASSWORD` | App Password for email | `abcd-efgh-ijkl` |

## 🚨 Troubleshooting
-   **500 Internal Server Error**: Check your logs! usually missing `DATABASE_URL` or `AI_API_KEY`.
-   **Database Error**: Ensure you installed `psycopg2-binary` (it's in requirements.txt now).
-   **Timeout**: If on Vercel, try Render/Railway.
