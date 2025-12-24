# pages/3_Settings.py
import streamlit as st
import sys
import os
import time
import importlib

# Fix path to imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

st.set_page_config(page_title="Settings", page_icon="⚙️")

st.title("⚙️ Settings")
st.markdown("Configure your email identity and AI Brain.")

with st.form("settings_form"):
    
    # --- AI SECTION ---
    st.subheader("🤖 AI Brain")
    
    ai_provider = st.selectbox(
        "AI Provider", 
        ["openai", "anthropic", "google", "custom"],
        index=["openai", "anthropic", "google", "custom"].index(config.AI_PROVIDER) if config.AI_PROVIDER in ["openai", "anthropic", "google", "custom"] else 0
    )
    
    col_ai1, col_ai2 = st.columns(2)
    
    ai_key_val = config.AI_API_KEY if config.AI_API_KEY else ""
    ai_model_val = config.AI_MODEL if config.AI_MODEL else ""
    ai_base_url_val = config.AI_BASE_URL if config.AI_BASE_URL else ""

    with col_ai1:
        ai_key = st.text_input("API Key", value=ai_key_val, type="password")
    
    with col_ai2:
        if ai_provider == "openai":
            ai_model = st.text_input("Model Name", value=ai_model_val, placeholder="gpt-3.5-turbo")
            ai_base_url = None
            st.caption("Default: gpt-3.5-turbo")
        elif ai_provider == "anthropic":
            ai_model = st.text_input("Model Name", value=ai_model_val, placeholder="claude-3-haiku-20240307")
            ai_base_url = None
            st.caption("Default: claude-3-haiku-20240307")
        elif ai_provider == "google":
            ai_model = st.text_input("Model Name", value=ai_model_val, placeholder="gemini-pro")
            ai_base_url = None
            st.caption("Default: gemini-pro")
        elif ai_provider == "custom":
            ai_model = st.text_input("Model Name", value=ai_model_val, placeholder="llama3-70b-8192")
            ai_base_url = st.text_input("Base URL", value=ai_base_url_val, placeholder="https://api.groq.com/openai/v1")
            st.caption("Use this for Groq, Perplexity, or Local LLMs (Ollama).")

    # --- EMAIL SECTION ---
    st.markdown("---")
    st.subheader("📧 Email Identity")
    st.info("We recommend using a dedicated Gmail account with an 'App Password'.")
    
    col_s1, col_s2 = st.columns(2)
    smtp_server = col_s1.text_input("SMTP Server", value=config.SMTP_SERVER)
    smtp_port = col_s2.number_input("SMTP Port", value=config.SMTP_PORT)
    
    smtp_user = st.text_input("SMTP Email (User)", value=config.SMTP_USER if config.SMTP_USER else "")
    smtp_pass = st.text_input("SMTP Password / App Password", value=config.SMTP_PASSWORD if config.SMTP_PASSWORD else "", type="password")
    sender_name = st.text_input("Your Name (Sender Name)", value=config.SENDER_NAME)
    
    if st.form_submit_button("✅ Save Configuration"):
        new_secrets = {
            "AI_PROVIDER": ai_provider,
            "AI_API_KEY": ai_key,
            "AI_MODEL": ai_model,
            "SMTP_SERVER": smtp_server,
            "SMTP_PORT": int(smtp_port),
            "SMTP_USER": smtp_user,
            "SMTP_PASSWORD": smtp_pass,
            "SENDER_NAME": sender_name
        }
        
        if ai_provider == "custom" and ai_base_url:
            new_secrets["AI_BASE_URL"] = ai_base_url
        
        if config.save_secrets(new_secrets):
            st.success(f"Saved! Using {ai_provider} provider.")
            # Reload config to apply changes immediately for the test
            importlib.reload(config)
            time.sleep(1)
            st.rerun()
        else:
            st.error("Failed to save settings.")

    # --- TEST CONNECTION SECTION ---
    st.markdown("---")
    st.subheader("🧪 Test AI Connection")
    if st.button("Ping AI Brain"):
        from src import ai_engine
        # Reload engine to pick up new config
        importlib.reload(ai_engine)
        
        with st.spinner(f"Testing {config.AI_PROVIDER}..."):
            # Simple prompt to verify connectivity
            test_response = ai_engine.generate_personalization({
                "Name": "Tester",
                "Company": "Test Corp",
                "Description": "A company that tests software connections."
            })
            
            if "Error" in test_response or "Please configure" in test_response:
                st.error(f"Test Failed: {test_response}")
                st.write("🔍 Checklist:")
                st.write("- Did you install requirements? (`pip install -r requirements.txt`)")
                st.write("- Is your API Key correct?")
                st.write("- If using Custom/Local, is the Server running?")
            else:
                st.success("✅ Connection Successful!")
                st.markdown(f"**AI Response:** _'{test_response}'_")
