# src/ai_engine.py
import os
import sys
import config
from src import data_manager

# Lazy checking for deps
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

def check_dependencies(provider):
    """Ensures the required package is installed for the chosen provider."""
    if provider == "openai" or provider == "custom":
        if OpenAI is None:
            return "Missing Dependency: Please run `pip install openai`"
    elif provider == "anthropic":
        if anthropic is None:
            return "Missing Dependency: Please run `pip install anthropic`"
    elif provider == "google":
        if genai is None:
            return "Missing Dependency: Please run `pip install google-generativeai`"
    return None

def get_knowledge_context(user_id):
    """
    Fetches context from the Knowledge Base.
    MERGES:
    1. Global Knowledge (is_global=True) -> Shared training data
    2. Private Knowledge (user_id=user_id) -> User specific data
    """
    db = next(data_manager.get_db())
    
    items = db.query(KnowledgeBase).filter(
        or_(
            KnowledgeBase.is_global == True,
            KnowledgeBase.user_id == user_id
        )
    ).limit(10).all() # Simple retrieval for now, RAG usually does vector search
    
    context = ""
    for item in items:
        context += f"[{item.category.upper()}]: {item.content}\n\n"
        
    db.close()
    return context

def get_system_prompt(lead_data, user_id=None):
    """Returns the prompt logic."""
    name = lead_data.get('Name', 'there')
    company = lead_data.get('Company', 'your company')
    desc = lead_data.get('Description', '')
    
    # 1. Fetch Knowledge Base
    kb_context = ""
    if user_id:
        kb_context = get_knowledge_context(user_id)
    else:
        # Fallback to global if no user_id provided or for backward compatibility
        kb_context = data_manager.get_knowledge_context()
    
    return f"""
    You are a B2B sales expert.
    
    {kb_context}
    
    Write a SINGLE sentence, personalized opening line for a cold email to {name} at {company}.
    
    Context about them: "{desc}"
    
    The line should be casual, specific to what they build, and compliment them. 
    Do NOT use "I hope you are doing well". 
    Do NOT mention "I saw on your website".
    Just state the observation.
    
    Example: "Saw you're building automation tools for small teams — felt this might align."
    """

def generate_with_openai(api_key, model, base_url, prompt):
    if not OpenAI: return "Error: openai package not installed."
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        response = client.chat.completions.create(
            model=model or "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=60,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"OpenAI Error: {e}"

def generate_with_anthropic(api_key, model, prompt):
    if not anthropic: return "Error: anthropic package not installed."
    
    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=model or "claude-3-haiku-20240307",
            max_tokens=60,
            temperature=0.7,
            system="You are a helpful assistant.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text.strip()
    except Exception as e:
        return f"Anthropic Error: {e}"

def generate_with_google(api_key, model, prompt):
    if not genai: return "Error: google-generativeai package not installed."
    
    genai.configure(api_key=api_key)
    try:
        model_name = model or "gemini-pro"
        m = genai.GenerativeModel(model_name)
        response = m.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini Error: {e}"

def generate_personalization(lead_data):
    """
    Generates a personalized opening line using the configured provider.
    """
    prompt = get_system_prompt(lead_data)
    
    provider = config.AI_PROVIDER
    api_key = config.AI_API_KEY
    model = config.AI_MODEL
    base_url = config.AI_BASE_URL
    
    if not api_key:
        return f"Please configure your {provider} API key in Settings."

    # Check if library is installed
    dep_error = check_dependencies(provider)
    if dep_error:
        return dep_error

    if provider == "openai":
        return generate_with_openai(api_key, model, None, prompt)
    elif provider == "anthropic":
        return generate_with_anthropic(api_key, model, prompt)
    elif provider == "google":
        return generate_with_google(api_key, model, prompt)
    elif provider == "custom":
        # Custom usually means an OpenAI-compatible endpoint (Groq, Perplexity, LocalLLM)
        return generate_with_openai(api_key, model, base_url, prompt)
    else:
        return "Unknown AI Provider configured."

def get_analysis_prompt(email_body):
    # Fetch KB
    kb_context = data_manager.get_knowledge_context()
    
    return f"""
    Analyze this email reply from a lead.
    
    {kb_context}
    
    Email Body:
    "{email_body}"
    
    Return a JSON object with:
    - "intent": One of ["Interested", "Not Interested", "OOO", "Unsubscribe", "Other"]
    - "sentiment": One of ["Positive", "Negative", "Neutral"]
    - "summary": A 1-sentence summary of what they said.
    
    Example JSON:
    {{
        "intent": "Interested",
        "sentiment": "Positive",
        "summary": "They asked for a demo next Tuesday."
    }}
    
    Return ONLY JSON.
    """

def analyze_reply(email_body):
    """
    Analyzes a reply to determine intent and sentiment.
    Returns dict: {'intent': ..., 'sentiment': ..., 'summary': ...}
    """
    prompt = get_analysis_prompt(email_body)
    
    provider = config.AI_PROVIDER
    api_key = config.AI_API_KEY
    model = config.AI_MODEL
    base_url = config.AI_BASE_URL
    
    if not api_key:
        return {"error": "Missing API Key"}

    # Reuse the same generation function but expect JSON
    # Ideally we'd switch to json_mode for OpenAI if supported
    
    result_text = ""
    if provider == "openai" or provider == "custom":
        result_text = generate_with_openai(api_key, model, base_url or None, prompt)
    elif provider == "anthropic":
        result_text = generate_with_anthropic(api_key, model, prompt)
    elif provider == "google":
        result_text = generate_with_google(api_key, model, prompt)
    else:
        result_text = "{}"

    # Parse JSON
    import json
    import re
    try:
        # Extract JSON if potential markdown wrapping
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
             return {"intent": "Other", "sentiment": "Neutral", "summary": result_text[:100]}
    except:
        return {"intent": "Other", "sentiment": "Neutral", "summary": "Failed to parse AI response."}
