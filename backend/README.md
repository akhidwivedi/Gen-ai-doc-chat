# DocChat Backend (Django REST + RAG)

Python 3.11+, Django, DRF, JWT, PostgreSQL, ChromaDB, Sentence Transformers, LangChain, Gemini/OpenAI.

## Quick start (macOS)

```bash
# 1. PostgreSQL (skip if you already have it)
brew install postgresql@16
brew services start postgresql@16
createdb docchat            # uses your mac user; see "DB user" note below

# 2. Python env
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt      # first install is large (PyTorch)

# 3. Config
cp .env.example .env
#  -> edit .env: set DB_USER/DB_PASSWORD, and GEMINI_API_KEY (or OPENAI_API_KEY + LLM_PROVIDER=openai)

# 4. Database + model warm-up
python manage.py migrate
python manage.py warmup_models       # downloads the ~90 MB embedding model once
python manage.py createsuperuser     # optional, for /admin/

# 5. Run
python manage.py runserver 8000
```

API is now at http://localhost:8000/api/ (health check: `/api/health/`).

**DB user note:** Homebrew Postgres creates a superuser named after your Mac login with no password.
Either set `DB_USER=<your mac username>` and leave `DB_PASSWORD` empty, or create a `postgres` role:
`createuser -s postgres && psql -c "ALTER USER postgres PASSWORD 'postgres';"`.

**No Postgres handy?** Set `DB_ENGINE=sqlite` in `.env` for a zero-setup run.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure dev key | Set a long random value outside local dev |
| `DJANGO_DEBUG` | `True` | |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | |
| `DB_ENGINE` | `postgres` | `postgres` or `sqlite` |
| `DB_NAME/USER/PASSWORD/HOST/PORT` | `docchat/postgres/""/localhost/5432` | |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Frontend origins |
| `JWT_ACCESS_MINUTES` / `JWT_REFRESH_DAYS` | `30` / `7` | |
| `LLM_PROVIDER` | `gemini` | `gemini` or `openai` |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | - / `gemini-2.5-flash` | Change the model name if Google retires it |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | - / `gpt-4o-mini` | |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | |
| `CHROMA_DIR` | `backend/chroma_db` | Vector DB persistence folder |
| `RAG_CHUNK_SIZE/OVERLAP/TOP_K/HISTORY_TURNS` | `1000/150/5/6` | |
| `MAX_UPLOAD_MB` | `20` | |

## Tests

```bash
python manage.py test
```
10 API tests: auth, upload validation (extension, size, magic bytes), user isolation (documents, chat, vectors),
document-specific chat history, summarize, delete cleanup. Embeddings and the LLM are faked, so they need no keys or downloads.

## API reference

Base URL `http://localhost:8000/api`. All endpoints except register/login/refresh/health need
`Authorization: Bearer <access_token>`.

### Auth
| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/auth/register/` | `{username, email, password}` | `201 {user, access, refresh}` |
| POST | `/auth/login/` | `{username, password}` | `200 {access, refresh}` |
| POST | `/auth/refresh/` | `{refresh}` | `200 {access}` |
| GET | `/auth/me/` | - | `{id, username, email}` |

### Documents (always scoped to the logged-in user; other users' ids return 404)
| Method | Path | Notes |
|---|---|---|
| GET | `/documents/` | List my documents |
| POST | `/documents/` | `multipart/form-data`: `file` (pdf/docx/txt), optional `title`. Extracts, chunks, embeds and indexes synchronously. Returns `201` with `status` = `ready` or `failed` (+ `error_message`) |
| GET | `/documents/{id}/` | Document detail |
| DELETE | `/documents/{id}/` | Deletes file, vectors and chat history |
| POST | `/documents/{id}/reprocess/` | Re-run indexing (e.g. after fixing a failure) |
| POST | `/documents/{id}/summarize/` | Generates and stores an LLM summary |

### Chat (history is per document, per user)
| Method | Path | Notes |
|---|---|---|
| GET | `/documents/{id}/chat/` | Full chat history, oldest first |
| POST | `/documents/{id}/chat/` | `{question}` -> `201 {user_message, assistant_message}`; assistant message includes `sources` (page, score, snippet) |
| DELETE | `/documents/{id}/chat/` | Clear history for this document |

### Misc
| GET | `/health/` | Liveness check |
|---|---|---|

Error codes: `400` validation, `401` unauthenticated, `404` not found / not yours, `409` document not ready,
`429` throttled, `503` LLM/config problem (message in `detail`).

## Architecture

```
config/            settings (env-driven), root urls
accounts/          register, login (JWT), refresh, me
documents/         Document model, upload validation, views, services.py (Django <-> AI glue)
chat/              ChatMessage model (FK document + user), chat endpoint
ai_services/       Framework-agnostic, reusable (no Django model imports):
  document_processing.py   PyMuPDF + python-docx text extraction
  chunking.py              LangChain RecursiveCharacterTextSplitter (keeps page numbers)
  embeddings.py            Sentence Transformers (lazy singleton)
  vector_store.py          ChromaDB; every query/delete filtered by user_id AND document_id
  llm.py                   Gemini / OpenAI via LangChain
  rag.py                   ingest_document, answer_question, summarize_document
```

### Security notes
- JWT auth on everything; throttling on auth, upload and chat endpoints.
- Document ownership checked on every request (`owner=request.user`); UUID primary keys.
- Vector search is filtered by user and document, so retrieval can't cross users.
- Uploads: extension allow-list, size limit, magic-byte check, random server-side filename in a per-user folder.
  Files are never served by URL (no `MEDIA_URL`), only read server-side.
- Set a real `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=False` before deploying anywhere public.

## Troubleshooting
- `psycopg.OperationalError ... role "postgres" does not exist` -> see DB user note above.
- First upload slow -> the embedding model is downloading; run `warmup_models` once.
- `GEMINI_API_KEY is not configured` (503 on chat) -> add the key to `.env` and restart the server.
- Scanned/image-only PDFs have no text and are marked `failed` (OCR is not included).
- Uploads are processed inside the request; very large files take a while. For production, move
  `process_document` to a task queue (Celery/RQ).
