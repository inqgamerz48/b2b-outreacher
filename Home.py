# Home.py (renamed from dashboard.py)
import streamlit as st
import pandas as pd
import os
import sys

# Add parent to path for imports to work in pages/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import data_manager
import config

st.set_page_config(
    page_title="B2B Outreach Manager",
    page_icon="🚀",
    layout="wide",
)

st.title("🚀 Outreach Command Center")

# Load Data
if not os.path.exists(config.DATA_FILE):
    data_manager.initialize_db()

df = data_manager.load_data()

# Metric Cards
total_leads = len(df)
sent_emails = len(df[df["Email_Sent"] == "Yes"])
replied = len(df[df["Replied"] == "Yes"])
pending = total_leads - sent_emails

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Leads", total_leads)
col2.metric("Emails Sent", sent_emails)
col3.metric("Pending Sent", pending)
col4.metric("Replies", replied)

st.markdown("---")

st.info("👈 Select a workflow step from the sidebar to get started.")

st.subheader("Recent Activity")
# Show last 5 added leads
if not df.empty:
    st.dataframe(df.tail(5), use_container_width=True)
else:
    st.caption("No data yet. Go to 'Find Leads' to start.")
