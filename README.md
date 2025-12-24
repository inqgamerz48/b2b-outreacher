# B2B Outreach System 🚀

A powerful, automated B2B cold outreach system designed to discover leads, enrich them with AI-generated personalization, and send cold emails efficiently.

## Features ✨

*   **Lead Discovery**: Scrapes potential leads based on queries (e.g., "SaaS Founder", "AI Agency Owner") using Google Search.
*   **AI Enrichment**: Uses LLMs (OpenAI, Anthropic, or Gemini) to generate hyper-personalized email opening lines based on the lead's company and description.
*   **Email Automation**: Sends cold emails with safety delays and daily limits to prevent spam flagging.
*   **Interactive Dashboard**: A Streamlit-based dashboard to track metrics, manage leads, and monitor campaign progress.
*   **Background Tasks**: Supports running scraping and sending tasks in the background via a persistent server.

## Prerequisites 🛠️

*   Python 3.9+
*   API Key for one of the supported AI providers:
    *   OpenAI (GPT-3.5/4)
    *   Anthropic (Claude)
    *   Google Gemini
*   SMTP Credentials for sending emails (e.g., Gmail App Password, SendGrid, etc.)

## Installation 📦

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd b2b-outreach
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration ⚙️

1.  Create a `.env` file in the root directory:
    ```bash
    copy .env.example .env  # (Or just create it manually)
    ```

2.  Add your configuration details to `.env`:
    ```ini
    # AI Configuration
    AI_PROVIDER=openai # openai, anthropic, google, or custom
    AI_API_KEY=sk-...
    AI_MODEL=gpt-3.5-turbo

    # Email Configuration
    SMTP_SERVER=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USERNAME=your_email@gmail.com
    SMTP_PASSWORD=your_app_password
    EMAIL_FROM=your_email@gmail.com
    DAILY_LIMIT=50
    ```

## Usage 🚀

### 1. Interactive Dashboard (Recommended)
Run the Streamlit dashboard to manage everything visually.
```bash
streamlit run Home.py
```

### 2. Command Line Interface (CLI)
You can also use the CLI for specific tasks.

*   **Scrape Leads:**
    ```bash
    python main.py scrape
    ```
*   **Enrich Leads (Generate AI Lines):**
    ```bash
    python main.py enrich
    ```
*   **Send Emails:**
    ```bash
    python main.py send
    ```

### 3. API Server
Run the FastAPI server to handle background tasks or programmatic access.
```bash
python server.py
```

## Project Structure 📂

*   `main.py`: CLI entry point.
*   `Home.py`: Streamlit dashboard entry point.
*   `server.py`: FastAPI backend.
*   `src/`: Core logic modules (scraper, ai_engine, email_sender, data_manager).
*   `data/`: Stores local database (Excel/CSV) and logs.
*   `pages/`: Additional Streamlit pages.

## License 📄
[MIT License](LICENSE)
