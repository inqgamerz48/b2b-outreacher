# 🚀 B2B Outreach Pro - Deployment Guide

**Welcome!** This guide will help you install, verify, and run your new AI Outreach System. 

---

## 📂 1. Project Organization
Your project is organized to be simple and clean:
- **`verify_system.py`**: The only file you need to run to check if everything works.
- **`server.py`**: The file to launch the application.
- **`src/`**: All the code logic (Back-end stuff).
- **`templates/`**: The website pages (HTML).
- **`import_hf.py`**: A special tool to "Train" your AI with more data.

---

## 🛠️ 2. Installation (First Time Only)
Before you start, you need to make sure your computer has the "libraries" installed.

1.  Open your terminal (PowerShell or Command Prompt).
2.  Navigate to this folder.
3.  Run this command:
    ```bash
    pip install -r requirements.txt
    ```
    *(If you don't have a requirements file yet, just ensure you have: `fastapi`, `uvicorn`, `sqlalchemy`, `requests`, `beautifulsoup4`, `jinja2`, `pytest`)*

---

## ✅ 3. Launching
1.  Run the server:
    ```bash
    python server.py
    ```
2.  Open **http://localhost:8000**
3.  Register your Admin user.

## 🧠 4. Admin Tools (Web UI)
- **System Health**: Go to `/brain` -> Click "Health".
- **AI Training**: Go to `/brain` -> Click "Auto-Train".

---

## ☁️ 6. Cloud Deployment (Heroku/Render)
To put this online so your team can use it:

1.  **Create a GitHub Repo** and upload these files.
2.  Connect your repo to **Render.com** (it's easiest).
3.  Render will ask for a "Start Command". Use:
    ```bash
    python server.py
    ```
4.  Add your `.env` variables (API Keys) in the Render dashboard.

**That's it! Enjoy your custom AI engine.** 
