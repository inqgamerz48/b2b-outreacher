# server.py
from fastapi import FastAPI, BackgroundTasks
from src import data_manager, scraper, email_sender
import uvicorn
import pandas as pd
import os

app = FastAPI(title="B2B Outreach System")

@app.get("/")
def read_root():
    return {"status": "running", "docs": "/docs"}

@app.get("/leads")
def get_leads():
    """Returns all leads in the database."""
    df = data_manager.load_data()
    # Replace NaN with null for JSON compatibility
    return df.where(pd.notnull(df), None).to_dict(orient="records")

@app.get("/stats")
def get_stats():
    """Returns simple stats about the leads."""
    df = data_manager.load_data()
    total = len(df)
    sent = len(df[df["Email_Sent"] == "Yes"])
    pending = total - sent
    return {
        "total_leads": total,
        "emails_sent": sent,
        "pending": pending
    }

@app.post("/trigger/scrape")
def trigger_scrape(background_tasks: BackgroundTasks):
    """Triggers scraping in the background."""
    # We define a wrapper to run the scraping logic
    def task():
        queries = ["AI agency founder", "SaaS founder"]
        leads = scraper.run_discovery(queries)
        for lead in leads:
            data_manager.add_lead(lead)
            
    background_tasks.add_task(task)
    return {"message": "Scraping started in background"}

@app.post("/trigger/send")
def trigger_send(background_tasks: BackgroundTasks):
    """Triggers email sending in the background."""
    background_tasks.add_task(email_sender.process_email_queue)
    return {"message": "Email sending started in background"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
