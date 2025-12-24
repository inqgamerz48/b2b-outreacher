# pages/1_Find_Leads.py
import streamlit as st
import time
import sys
import os

# Fix path to imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import scraper, data_manager

st.set_page_config(page_title="Find Leads", page_icon="🔍")

st.title("🔍 Find Potential Clients")
st.markdown("Enter your target niche below. We'll search for founders and owners.")

with st.form("scraping_form"):
    search_queries = st.text_area("Who are we looking for? (e.g. 'AI Agency Founder London')", height=150)
    submitted = st.form_submit_button("🚀 Start Discovery")

if submitted and search_queries:
    queries = [q.strip() for q in search_queries.split("\n") if q.strip()]
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    status_text.text("Searching Google...")
    
    # We can't stream results easily from the synchronous scraper function without refactoring,
    # so we'll just run it. (Future improvement: Make scraper yield results).
    
    new_leads = scraper.run_discovery(queries)
    progress_bar.progress(50)
    status_text.text("Processing results...")
    
    added_count = 0
    for lead in new_leads:
        if data_manager.add_lead(lead):
            added_count += 1
            
    progress_bar.progress(100)
    status_text.text("Done!")
    
    if added_count > 0:
        st.success(f"🎉 Found and added {added_count} new unique leads!")
        st.balloons()
    else:
        st.warning("Found leads, but they were already in your database (or no emails found).")
