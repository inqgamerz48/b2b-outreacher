from fastapi import FastAPI, BackgroundTasks, Request, Response, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src import data_manager, scraper, email_sender, campaign_manager, account_manager, auth
from src.data_manager import Lead, Campaign, SMTPAccount, KnowledgeBase, User, get_db


app = FastAPI(title="B2B Outreach Pro")

# Setup Templates
# Setup Templates
templates = Jinja2Templates(directory="templates")

# Custom Filters
def url_to_domain(url):
    if not url: return ""
    try:
        from urllib.parse import urlparse
        if not url.startswith("http"):
            url = "http://" + url
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return ""

templates.env.filters["domain"] = url_to_domain

# Server Location Cache
SERVER_LOCATION = {"city": "Unknown", "country": "Unknown", "query": "127.0.0.1"}
try:
    print("[INFO] Fetching Server Location...")
    import requests
    resp = requests.get("http://ip-api.com/json/", timeout=2)
    if resp.status_code == 200:
        SERVER_LOCATION = resp.json()
        try:
            print(f"[INFO] Server Location: {SERVER_LOCATION.get('city')}, {SERVER_LOCATION.get('country')}")
        except:
            print("[INFO] Server Location: (Unicode Name)")
except Exception as e:
    print(f"[WARN] Could not fetch location: {e}")

# --- Middleware / Dependency ---
async def get_current_user(request: Request):
    """
    Dependency to check if user is logged in via cookie.
    Simple session check: cookie 'session_user' should exist.
    In prod, sign this cookie or use JWT.
    """
    user = request.cookies.get("session_user")
    if not user:
        return None
    return user

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Public routes
    if request.url.path in ["/login", "/register", "/static", "/favicon.ico"]:
        response = await call_next(request)
        return response
    
    # Check valid cookie
    user = request.cookies.get("session_user")
    if not user:
        # If API call, return 401? For now assume browser only app
        # If trying to access protected page, redirect to login
        return RedirectResponse(url="/login")
        
    response = await call_next(request)
    return response


# --- Auth Routes ---

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...)):
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    db.close()
    
    if user and auth.verify_password(password, user.password_hash):
        # Success
        resp = RedirectResponse(url="/dashboard", status_code=303)
        resp.set_cookie(key="session_user", value=user.username, httponly=True)
        return resp
    else:
        return templates.TemplateResponse("login.html", {"request": {}, "error": "Invalid credentials"})

@app.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("session_user")
    return resp

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    db = next(get_db())
    if db.query(User).filter(User.username == username).first():
        db.close()
        return templates.TemplateResponse("register.html", {"request": {}, "error": "Username already taken"})
    
    # Create User
    hashed_pw = auth.get_password_hash(password)
    user = User(username=username, password_hash=hashed_pw)
    db.add(user)
    db.commit()
    db.close()
    
    # Redirect to Login with success message (or just login logic)
    # For now, redirect to login
    return RedirectResponse(url="/login", status_code=303)


# --- Protected Routes ---

# Helper to get user obj
def get_user_from_request(request: Request, db):
    username = request.cookies.get("session_user")
    if not username: return None
    return db.query(User).filter(User.username == username).first()

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """
    Public Landing Page.
    Redirects to dashboard if already logged in.
    """
    db = next(get_db())
    user = get_user_from_request(request, db)
    db.close()
    
    if user:
        return RedirectResponse("/dashboard")
    
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Main Dashboard View (Protected).
    """
    db = next(get_db())
    user = get_user_from_request(request, db)
    if not user:
        db.close()
        return RedirectResponse("/login")
        
    # Text Stats (Scoped)
    total_leads = db.query(Lead).filter_by(user_id=user.id).count()
    emails_sent = db.query(Lead).filter_by(user_id=user.id).filter(Lead.status.in_(['Contacted', 'Replied'])).count()
    replies = db.query(Lead).filter_by(user_id=user.id).filter(Lead.status == "Replied").count()
    active_campaigns = db.query(Campaign).filter_by(user_id=user.id).filter(Campaign.status == "Active").count()
    
    reply_rate = round((replies / emails_sent * 100), 1) if emails_sent > 0 else 0
    
    stats = {
        "total_leads": total_leads,
        "emails_sent": emails_sent,
        "replies": replies,
        "reply_rate": reply_rate,
        "active_campaigns": active_campaigns
    }
    
    # Recent Activity (Scoped)
    recent_activity = []
    recent_leads = db.query(Lead).filter_by(user_id=user.id).order_by(Lead.last_contacted_at.desc()).limit(5).all()
    for lead in recent_leads:
        if lead.last_contacted_at:
            recent_activity.append({
                "type": "Sent",
                "title": f"Sent email to {lead.email}",
                "time": lead.last_contacted_at.strftime("%H:%M")
            })
            
    db.close()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "page": "dashboard",
        "stats": stats,
        "recent_activity": recent_activity,
        "username": user.username,
        "server_location": SERVER_LOCATION
    })

@app.get("/campaigns", response_class=HTMLResponse)
async def campaigns_page(request: Request):
    db = next(get_db())
    user = get_user_from_request(request, db)
    if not user: 
        db.close()
        return RedirectResponse("/login")

    campaigns_orm = db.query(Campaign).filter_by(user_id=user.id).all()
    campaigns = []
    for c in campaigns_orm:
        campaigns.append({
            "name": c.name,
            "status": c.status,
            "leads_count": len(c.leads),
            "created_at": c.created_at
        })
    db.close()
    
    return templates.TemplateResponse("campaigns.html", {
        "request": request,
        "page": "campaigns",
        "campaigns": campaigns,
        "username": user.username
    })

@app.post("/campaigns/create")
async def create_campaign(request: Request, name: str = Form(...)):
    db = next(get_db())
    user = get_user_from_request(request, db)
    if user:
        campaign_manager.create_campaign(name, [], user_id=user.id) # Updated signature
    db.close()
    return RedirectResponse(url="/campaigns", status_code=303)

@app.get("/leads", response_class=HTMLResponse)
async def leads_page(request: Request):
    db = next(get_db())
    user = get_user_from_request(request, db)
    if not user:
        db.close()
        return RedirectResponse("/login")
        
    leads = db.query(Lead).filter_by(user_id=user.id).order_by(Lead.id.desc()).limit(100).all()
    db.close()
    
    return templates.TemplateResponse("leads.html", {
        "request": request,
        "page": "leads",
        "leads": leads,
        "username": user.username
    })

@app.get("/brain", response_class=HTMLResponse)
async def brain_page(request: Request):
    """
    Brain/Knowledge Base View.
    Shows BOTH Private (user_id) and Global (is_global=True) items.
    """
    db = next(get_db())
    user = get_user_from_request(request, db)
    if not user:
        db.close()
        return RedirectResponse("/login")
        
    # Fetch Private + Global
    from sqlalchemy import or_
    knowledge = db.query(KnowledgeBase).filter(
        or_(
            KnowledgeBase.user_id == user.id,
            KnowledgeBase.is_global == True
        )
    ).order_by(KnowledgeBase.created_at.desc()).all()
    db.close()
    
    return templates.TemplateResponse("brain.html", {
        "request": request,
        "page": "brain",
        "knowledge": knowledge,
        "username": user.username
    })

@app.post("/brain/add")
async def add_knowledge(request: Request, category: str = Form(...), content: str = Form(...)):
    db = next(get_db())
    user = get_user_from_request(request, db)
    if user:
        # User adds PRIVATE knowledge by default
        item = KnowledgeBase(user_id=user.id, category=category, content=content, is_global=False)
        db.add(item)
        db.commit()
    db.close()
    return RedirectResponse(url="/brain", status_code=303)

@app.post("/brain/delete/{item_id}")
async def delete_knowledge(request: Request, item_id: int):
    db = next(get_db())
    user = get_user_from_request(request, db)
    if user:
        # Only delete if user owns it
        db.query(KnowledgeBase).filter_by(id=item_id, user_id=user.id).delete()
        db.commit()
    db.close()
    return RedirectResponse(url="/brain", status_code=303)

# --- API Endpoints (kept for background tasks) ---

@app.post("/trigger/scrape")
def trigger_scrape(background_tasks: BackgroundTasks):
    """Triggers scraping in the background."""
    def task():
        queries = ["AI agency founder", "SaaS founder"]
        leads = scraper.run_discovery(queries)
        for lead in leads:
             # Basic add logic (would need to be improved to use DB session directly)
             pass 
    background_tasks.add_task(task)
    return {"message": "Scraping started"}

@app.post("/trigger/send")
def trigger_send(background_tasks: BackgroundTasks):
    background_tasks.add_task(email_sender.process_email_queue)
    return {"message": "Sending started"}

@app.get("/settings", response_class=HTMLResponse)
async def settings_view(request: Request):
    """
    User Settings Page.
    """
    db = next(get_db())
    user = get_user_from_request(request, db)
    # Pass current config to template for pre-filling
    import config
    current_config = {
        "AI_PROVIDER": config.AI_PROVIDER,
        "AI_API_KEY": config.AI_API_KEY,
        "AI_MODEL": config.AI_MODEL
    }
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "page": "settings",
        "username": user.username,
        "config": current_config
    })

@app.post("/settings/update")
async def update_settings(
    request: Request, 
    ai_provider: str = Form(...), 
    ai_api_key: str = Form(""),
    ai_model: str = Form("")
):
    import config
    
    # Save to secrets.json
    new_secrets = {
        "AI_PROVIDER": ai_provider,
        "AI_API_KEY": ai_api_key,
        "AI_MODEL": ai_model
    }
    
    if config.save_secrets(new_secrets):
        # Reload config in memory (simple hack, improved in prod)
        config._secrets = config.load_secrets()
        config.AI_PROVIDER = config.get_config("AI_PROVIDER")
        config.AI_API_KEY = config.get_config("AI_API_KEY")
        config.AI_MODEL = config.get_config("AI_MODEL")
        
        return RedirectResponse(url="/settings?msg=Settings Saved", status_code=303)
    else:
        return RedirectResponse(url="/settings?error=Failed to save", status_code=303)

@app.get("/inbox", response_class=HTMLResponse)
async def inbox_view(request: Request):
    """
    Inbox View (Leads with Replied status).
    """
    db = next(get_db())
    user = get_user_from_request(request, db)
    if not user:
        db.close()
        return RedirectResponse("/login")
    
    # Fetch leads with 'Replied' status (or just list all contacted for now as a fallback if no replies)
    # For a real inbox we'd want Replied. Let's show "Replied" and "Contacted" so list isn't empty for demo.
    leads = db.query(Lead).filter_by(user_id=user.id).filter(
        Lead.status.in_(['Replied', 'Contacted'])
    ).order_by(Lead.last_contacted_at.desc()).all()
    
    db.close()
    
    return templates.TemplateResponse("inbox.html", {
        "request": request,
        "page": "inbox",
        "leads": leads,
        "username": user.username
    })

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# --- Cloud Admin Routes ---

@app.post("/admin/train")
async def admin_train(request: Request, background_tasks: BackgroundTasks):
    db = next(get_db())
    user = get_user_from_request(request, db)
    if not user:
        db.close()
        return RedirectResponse("/login")
    db.close()

    # Run in background
    from src import ai_trainer
    background_tasks.add_task(ai_trainer.import_hf_data)
    
    return RedirectResponse(url="/brain?msg=Training Started in Background", status_code=303)

@app.get("/admin/health", response_class=HTMLResponse)
async def admin_health(request: Request):
    """
    Runs the system verification suite and shows a report card.
    """
    db = next(get_db())
    user = get_user_from_request(request, db)
    if not user:
        db.close()
        return RedirectResponse("/login")
    db.close() # Close quickly
    
    # Run Pytest and capture output
    import pytest
    from io import StringIO
    
    # Redirect stdout to capture test output
    capture = StringIO()
    old_stdout = sys.stdout
    sys.stdout = capture
    
    try:
        # Run tests/test_system.py
        # clean output, verbose
        exit_code = pytest.main(["-v", "tests/test_system.py"])
    except Exception as e:
        exit_code = 1
        print(f"Test Execution Failed: {e}")
    finally:
        sys.stdout = old_stdout # Restore stdout
        
    output_log = capture.getvalue()
    status = "Healthy" if exit_code == 0 else "Issues Detected"
    color = "text-emerald-600 font-bold" if exit_code == 0 else "text-red-600 font-bold"
    
    html_report = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>System Health</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>@import url('https://fonts.googleapis.com/css2?family=Inter:300,400,600&display=swap'); body {{ font-family: 'Inter', sans-serif; }}</style>
    </head>
    <body class="bg-gray-50 p-10">
        <div class="max-w-4xl mx-auto bg-white p-8 rounded-xl shadow-lg">
            <div class="flex justify-between items-center mb-6">
                <h1 class="text-2xl font-bold text-gray-800">System Health Report</h1>
                <a href="/dashboard" class="text-blue-600 hover:underline">Back to Dashboard</a>
            </div>
            
            <div class="mb-6 p-4 bg-gray-50 rounded border border-gray-200">
                <p class="text-lg">Status: <span class="{color}">{status}</span></p>
            </div>
            
            <div class="bg-black text-green-400 p-4 rounded font-mono text-sm overflow-x-auto whitespace-pre">
{{output_log}}
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_report)

if __name__ == "__main__":
    print("[INFO] Cloud Server Starting...")
    print("[INFO] Initializing Database...")
    data_manager.initialize_db()
    print("[INFO] DB Ready. Listening on 0.0.0.0:8000")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
