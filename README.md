# DocChat - chat with your documents (RAG)

Upload PDF/DOCX/TXT files and ask questions about each one. Separate React frontend and Django REST backend.

| Layer | Stack |
|---|---|
| Frontend | React, Vite, JavaScript, Axios, Tailwind CSS |
| Backend | Python 3.11+, Django, DRF, JWT (simplejwt) |
| GenAI | Gemini or OpenAI, LangChain, Sentence Transformers, RAG |
| Vector DB | ChromaDB |
| Documents | PyMuPDF, python-docx |
| Database | PostgreSQL |

## Run it (two terminals)

```bash
# Terminal 1 - backend (details: backend/README.md)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add GEMINI_API_KEY (or OPENAI_API_KEY), DB settings
createdb docchat
python manage.py migrate
python manage.py warmup_models
python manage.py runserver 8000

# Terminal 2 - frontend (details: frontend/README.md)
cd frontend
cp .env.example .env
npm install
npm run dev                     # http://localhost:5173
```

## Docs
- [backend/README.md](backend/README.md): setup, env vars, full API endpoint list, architecture, security
- [frontend/README.md](frontend/README.md): setup, structure

## Request flow
1. Upload -> validated (type, size, magic bytes) -> saved under the user's folder -> text extracted -> chunked -> embedded -> stored in ChromaDB tagged with `user_id` + `document_id`.
2. Question -> embed -> retrieve top-k chunks filtered by user + document -> LLM answers from those chunks with the last few turns of that document's chat -> saved to history with sources.
