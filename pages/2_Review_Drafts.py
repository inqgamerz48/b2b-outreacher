# pages/2_Review_Drafts.py
import streamlit as st
import pandas as pd
import sys
import os
import time

# Fix path to imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import data_manager, ai_engine, email_sender
import config

st.set_page_config(page_title="Draft Room", page_icon="✍️", layout="wide")

st.title("✍️ The Draft Room")
st.markdown("Review and approve AI-generated drafts before sending.")

# Load Data
df = data_manager.load_data()

# 1. Filter for Pending Enrichment
# Leads that need AI lines but haven't been sent
needs_enrichment = df[
    (df["Personalization_Line"].isna() | (df["Personalization_Line"] == "")) & 
    (df["Email_Sent"] == "No")
]

if not needs_enrichment.empty:
    st.info(f"✨ You have {len(needs_enrichment)} leads waiting for AI drafting.")
    if st.button("Generate Drafts for All"):
        with st.spinner("Writing drafts..."):
            progress_bar = st.progress(0)
            total = len(needs_enrichment)
            count = 0
            for index, row in needs_enrichment.iterrows():
                lead_dict = row.to_dict()
                line = ai_engine.generate_personalization(lead_dict)
                df.at[index, "Personalization_Line"] = line
                count += 1
                progress_bar.progress(count / total)
            
            data_manager.save_data(df)
            st.success("Drafts generated! Reloading...")
            time.sleep(1)
            st.rerun()

# 2. Review & Send Interface
# Filter for leads that HAVE a draft but are NOT sent
ready_to_review = df[
    (df["Personalization_Line"].notna()) & 
    (df["Personalization_Line"] != "") & 
    (df["Email_Sent"] == "No")
]

if ready_to_review.empty:
    st.success("All caught up! No drafts to review.")
else:
    st.write(f"**{len(ready_to_review)} Drafts Ready for Review**")
    
    # Show one at a time or a list? 
    # For MLP, an expander list is easiest to manage.
    
    for index, row in ready_to_review.head(10).iterrows(): # pagination limit
        with st.expander(f"Draft for: {row['Name']} @ {row['Company']}", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Editable Draft
                current_line = row["Personalization_Line"]
                new_line = st.text_area("Personalization Line", value=current_line, key=f"text_{index}")
                
                # Preview full email
                st.markdown("**Preview:**")
                st.caption(f"""
                Hi {row['Name'].split()[0] if row['Name'] else 'there'},
                
                {new_line}
                
                I'm building a tool that helps agencies... [Rest of Template]
                """)
            
            with col2:
                st.write("**Lead Info**")
                st.write(f"🔗 {row['Website']}")
                st.write(f"📝 {row['Description'][:100]}...")
                
                if st.button("🚀 Approve & Send", key=f"send_{index}"):
                    # Save any edits first
                    df.at[index, "Personalization_Line"] = new_line
                    data_manager.save_data(df)
                    
                    # Convert row to dict and send
                    lead_dict = df.loc[index].to_dict()
                    if email_sender.send_email(lead_dict):
                        st.balloons()
                        st.success(f"Sent to {row['Email']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to send. Check SMTP settings.")
                
                if st.button("🗑️ Discard Lead", key=f"discard_{index}"):
                    # We can just mark as skipped or delete. For now, let's delete row.
                    df = df.drop(index)
                    data_manager.save_data(df)
                    st.rerun()
