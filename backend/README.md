# Job_tracker (Email → LLM → MongoDB job extractor)

MVP: FastAPI backend that:
- Connects to Gmail via OAuth Web Application flow
- Polls job-related emails on a schedule (APScheduler)
- Extracts structured fields using OpenAI
- Stores results in MongoDB Atlas

## Prereqs (Windows)
- Python 3.10+ recommended
- A MongoDB Atlas cluster + connection string
- Google Cloud project with Gmail API enabled
- OpenAI API key

## 1) Setup Google OAuth (Web Application)
1. Go to Google Cloud Console → APIs & Services
2. Enable Gmail API
3. Configure OAuth consent screen (External is fine for MVP)
4. Credentials → Create Credentials → OAuth client ID
   - Application type: Web application
   - Authorized redirect URIs:
     - http://localhost:8000/api/gmail/oauth/callback

Copy your Client ID and Client Secret into .env.

## 2) Configure environment
Create backend/.env (copy from backend/.env.example) and fill in:
- MONGODB_URI (Atlas URI)
- MONGODB_DB (e.g. job_tracker)
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_REDIRECT_URI (default is fine)
- OPENAI_API_KEY

## 3) Install + run (Windows PowerShell)
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Run the API:
uvicorn app.main:app --reload --port 8000

## 4) Connect Gmail
1. Open:
   http://localhost:8000/api/gmail/oauth/start
2. Copy the auth_url into your browser and authorize.
3. After success, token is stored locally at:
   backend/.gmail_token.json

## 5) Scheduler + pipeline
Scheduler starts automatically on API startup (every 60 minutes by default).
To manually trigger a fetch/extract:
- Call: POST http://localhost:8000/api/jobs/run-once

To view saved jobs:
- Call: GET http://localhost:8000/api/jobs/latest

## Notes / Limitations (MVP)
- Tokens are stored locally in backend/.gmail_token.json (not production-safe).
- OAuth refresh handling is included via Google credentials.
- Extraction quality depends on the email content and model.

## Next improvements
- Store tokens in MongoDB keyed to user
- Add deduping based on thread/message hash
- Add UI (Next.js) for browsing jobs
- Add domain allow/deny lists and richer query rules
