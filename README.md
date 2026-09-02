# AI Study Copilot

AI Study Copilot is a planned personalized study platform designed to help students organize learning materials, practise effectively, and understand their progress.

## Planned features

- Study material uploads and document processing
- AI study chat and question answering
- Quiz and flashcard generation
- Performance analysis and weak-topic detection
- Exam-topic intelligence and personalized revision planning

## Planned technology stack

- **Frontend:** React, Vite, Tailwind CSS
- **Backend:** Python, FastAPI
- **Database:** PostgreSQL (with pgvector planned for a later phase)
- **AI/ML:** LLM APIs and embedding models (planned for later phases)
- **Document processing:** PDF, PPTX, DOCX parsing and OCR (planned for later phases)

## Current status

This repository contains the initial project foundation only. It provides a React/Vite frontend shell, a minimal FastAPI service with a health endpoint, PostgreSQL development configuration, and project documentation directories. No application features, authentication, AI workflows, retrieval, quizzes, OCR, or study logic have been implemented.

This is an early development version and its structure may evolve as the product is designed and built.

## Getting started

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend health check is available at `GET /health`.

### Database

Copy `.env.example` to `.env`, update local values as needed, then start PostgreSQL:

```bash
docker compose up -d postgres
```
