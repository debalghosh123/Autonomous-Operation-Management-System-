# Career Lab Consulting - Python Evaluation System

AI-powered Python evaluation platform with Groq AI integration, built with FastAPI.

## Features

- **25 Python Questions** - 4 marks each, 100 total marks
- **90% to Qualify** - Rigorous evaluation standard
- **Groq AI Feedback** - Personalized AI-powered performance analysis
- **Voice Mode** - Accessibility-focused voice commands via Web Speech API
- **Admin Panel** - Complete dashboard with statistics and candidate management
- **Email Notifications** - Automated result delivery via SMTP
- **WhatsApp Integration** - Exam results via Twilio WhatsApp API
- **Dark Theme** - Career Lab branded dark UI
- **Railway Ready** - One-click deployment to Railway

## Tech Stack

- **Backend:** FastAPI + Python 3.11
- **AI:** Groq API (LLaMA 3.1 70B)
- **Database:** SQLite (WAL mode)
- **Frontend:** Jinja2 + HTML/CSS/JS
- **Notifications:** SMTP + Twilio WhatsApp
- **Deploy:** Railway / Docker

## Quick Start

```bash
# Clone the repository
git clone https://github.com/debalghosh123/Autonomous-Operation-Management-System-.git
cd Autonomous-Operation-Management-System-

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
python main.py
```

Visit http://localhost:8000

## Deployment to Railway

1. Push to GitHub
2. Connect repository in Railway
3. Add environment variables in Railway dashboard
4. Deploy automatically via Dockerfile

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| GROQ_API_KEY | Groq AI API key | Yes (for AI feedback) |
| SECRET_KEY | Application secret | Yes |
| SMTP_USER | Email username | No |
| SMTP_PASSWORD | Email password | No |
| TWILIO_ACCOUNT_SID | Twilio SID | No |
| TWILIO_AUTH_TOKEN | Twilio token | No |
| ADMIN_USERNAME | Admin login | No (default: admin) |
| ADMIN_PASSWORD | Admin password | No (default: admin123) |

## API Endpoints

- `GET /` - Landing page
- `GET /register` - Registration form
- `POST /register` - Register candidate
- `GET /exam/start/{id}` - Start exam
- `GET /exam/questions/{id}` - Exam questions
- `POST /exam/submit/{id}` - Submit exam
- `GET /exam/result/{id}` - View results
- `GET /admin/login` - Admin login
- `GET /admin/dashboard` - Admin dashboard
- `GET /api/health` - Health check
- `POST /api/candidates` - Create candidate (API)
- `GET /api/statistics` - Get statistics
- `POST /api/voice` - Voice commands

## Exam Configuration

- Total Questions: 25
- Marks per Question: 4
- Total Marks: 100
- Passing Percentage: 90%
- Duration: 60 minutes

## License

Copyright 2024 Career Lab Consulting. All rights reserved.
