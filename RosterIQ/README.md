# RosterIQ

Submission-ready project package for HiLabs AgentX AI 2026.

## Quick Start

1. Install backend dependencies.

```bash
pip install -r requirements.txt
```

2. Create environment file.

```bash
copy .env.example .env
```

3. Run backend.

```bash
uvicorn backend.main:app --reload
```

4. Run frontend in a new terminal.

```bash
cd frontend
npm install
npm start
```

## Required Environment Variables

- GROQ_API_KEY
- TAVILY_API_KEY
- FIREBASE_PROJECT_ID
- FIREBASE_CLIENT_EMAIL
- FIREBASE_PRIVATE_KEY
- FASTAPI_ENV
- REACT_APP_API_BASE_URL (optional override)

## Judge-Facing Endpoints

- GET /procedures
- POST /procedures/{name}/run
- GET /memory/status
- GET /analytics/pipeline-report?state=CA
- POST /ask

## Validation

Run smoke tests from the `RosterIQ` folder:

```bash
python -m unittest backend.tests.test_judging_readiness
```

## Documentation Index

- docs/README.md
- docs/architecture_diagram.md
- docs/system_flow.md
- docs/demo_script.md
- docs/SUBMISSION_CHECKLIST.md

## Security Notes

- Never commit `.env`.
- Keep repository private for submission.
- Share read access only with the required judge usernames.
