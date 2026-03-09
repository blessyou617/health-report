# Health Report API

AI-powered health checkup report analysis backend.

## Tech Stack

- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **File Storage**: Local / Object Storage (OSS)

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Run database migrations
alembic upgrade head

# 4. Start server
uvicorn app.main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | WeChat login |
| POST | `/upload/report` | Upload health report |
| POST | `/questionnaire/submit` | Submit lifestyle questionnaire |
| POST | `/analyze/report/{report_id}` | AI analysis |
| POST | `/qa/ask` | Ask follow-up question |
| GET | `/report/{report_id}` | Get report details |

## Project Structure

```
app/
├── core/           # Core configurations
├── models/        # Database models
├── routers/       # API routes
├── services/     # Business logic
└── main.py       # Application entry
```
