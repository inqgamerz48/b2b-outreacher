# 🚀 B2B Outreach Pro (SaaS Edition)

**The Ultimate AI-Powered Outreach Engine.**  
*Self-Hosted, Multi-Tenant, and Self-Learning.*

![Dashboard Preview](https://cdn.dribbble.com/users/411475/screenshots/16279163/media/4c776483568c04ec52431770956973e6.png) 
*(Note: Placeholder image, actual UI is built with TailwindCSS)*

---

## 🌟 Features

### 🧠 1. Self-Learning AI Brain (RAG)
- **Custom Knowledge**: Feed it your case studies, tone guides, and offers.
- **Auto-Training**: Enriches the model with 1000+ curated business communication examples.
- **Context Aware**: Every message is hyper-personalized using your unique brain data.

### 🫧 2. Multi-Tenant SaaS Architecture
- **User "Bubbles"**: Strictly isolates data between users. A perfect foundation for selling this as a SaaS.
- **Global vs. Private Memory**: All users share the "Global" master knowledge base, but keep their own "Private" offers/data secret.

### 📧 3. Advanced Engagement Engine
- **Smart Drip Sequences**: Visual campaign builder with delays and follow-ups.
- **Inbox Rotation**: Load balance sending across multiple accounts to ensure high deliverability and compliance.
- **Public Data Discovery**: Ethically finds business contact information from publicly available web pages.
- **Reply Monitor**: AI reads replies and categorizes them (Interested, OOO, Not Interested).

### 🎨 4. Modern UI & Security
- **Tech**: FastAPI + Jinja2 + TailwindCSS.
- **Auth**: Secure Login/Registration with hashed passwords.
- **Dashboard**: Real-time charts and activity feeds.

---

## 🛠️ Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Verify System
Run the automated diagnostic suite to ensure DB, Auth, and AI are healthy.
```bash
python verify_system.py
```

### 3. Launch
```bash
python server.py
```
Visit **http://localhost:8000**
- **Default Admin**: `admin` / `password123`
- Or click **"Create Account"** to register a new user.

### 4. Train the Brain (Optional)
Pull ~1200 training examples from the web:
```bash
python import_hf.py
```

---

## 📂 Project Structure
- **`src/`**: Core logic (AI, Scraper, Emailer).
- **`templates/`**: HTML Frontend (Tailwind).
- **`tests/`**: Pytest suite.
- **`archive/`**: Old scripts.
- **`DEPLOYMENT.md`**: Detailed guide for pushing to Cloud (Render/Heroku).

---

## 🛡️ License
Proprietary / Closed Source.
Built for the User.
