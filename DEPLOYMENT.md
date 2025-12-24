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

## ✅ 3. Verification (Pre-Flight Check)
Before you fly, you must check the engine. I have built a master tool for this.

1.  Run the verification scanner:
    ```bash
    python verify_system.py
    ```
2.  **Look for green checks**. If it says **"ALL SYSTEMS OPERATIONAL"**, you are good to go.

---

## 🚀 4. Launching the App
Now, let's turn it on.

1.  Run the server:
    ```bash
    python server.py
    ```
2.  Open your browser and visit:
    👉 **http://localhost:8000**

3.  **Log In**:
    - Click **"Create Account"** to register your Admin user.
    - The first registered user acts as the system owner.

---

## 🧠 5. Enhancing the AI (Optional)
Want to make the AI smarter?
1.  Run the enrichment script:
    ```bash
    python import_hf.py
    ```
    *This will ingest 1000+ curated examples to improve generation quality.*

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
