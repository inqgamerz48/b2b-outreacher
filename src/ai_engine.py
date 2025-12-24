# src/ai_engine.py
import os
import sys
import config

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

def get_system_prompt(lead_data):
    """Returns the prompt logic."""
    name = lead_data.get('Name', 'there')
    company = lead_data.get('Company', 'your company')
    desc = lead_data.get('Description', '')
    
    return f"""
    You are a B2B sales expert. Write a SINGLE sentence, personalized opening line for a cold email to {name} at {company}.
    
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
