# LLM Document QA System

A document question-answering system powered by a language model. Users upload documents; the system automatically extracts text, splits it into chunks, generates embeddings, stores them in a vector database, and answers questions based on document content using Retrieval-Augmented Generation (RAG).

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [How to Use the System](#how-to-use-the-system)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Technical Decisions](#technical-decisions)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)

---

## Features

- ✅ Document management (add, edit, delete) via API or Django Admin
- ✅ Support for `.docx` files and raw text (including Word tables)
- ✅ Automatic text extraction and storage
- ✅ Semantic chunking with LangChain
- ✅ Multilingual embeddings (Persian, English, and 50+ languages)
- ✅ Vector storage in Qdrant
- ✅ Fast semantic search
- ✅ RAG-based answers grounded in document content
- ✅ Source attribution (answers link back to chunks)
- ✅ Question and answer history
- ✅ Full REST API with Django REST Framework + Swagger docs
- ✅ Fully containerized with Docker

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                        Client                            │
│              (Browser / Postman / curl)                  │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP
                         ▼
┌──────────────────────────────────────────────────────────┐
│              Django + DRF (Web Service)                  │
│  ┌────────────────────┐    ┌─────────────────────────┐   │
│  │   documents app    │    │        qa app           │   │
│  │  Document          │    │   Question              │   │
│  │  DocumentChunk     │    │   services.py (RAG)     │   │
│  │  utils / embeddings│    │                         │   │
│  └─────────┬──────────┘    └──────────┬──────────────┘   │
└────────────┼───────────────────────────┼─────────────────┘
             │                           │
             ▼                           ▼
      ┌────────────┐              ┌────────────┐
      │ PostgreSQL │              │   Qdrant   │
      │ (Metadata) │              │ (Vectors)  │
      └────────────┘              └─────┬──────┘
                                        │
                          ┌─────────────┴─────────────┐
                          ▼                           ▼
                   ┌─────────────┐            ┌─────────────┐
                   │ HuggingFace │            │     LLM     │
                   │ Embeddings  │            │ (HF/Ollama) │
                   └─────────────┘            └─────────────┘
```

| Component | Purpose |
|-----------|---------|
| **Django + DRF** | Web framework, ORM, API, Admin Panel |
| **PostgreSQL** | Stores document, chunk, and question metadata |
| **Qdrant** | Vector database for semantic search |
| **HuggingFace** | Multilingual embedding model (local, offline) |
| **LLM** | Answer generation (HuggingFace Inference or Ollama) |
| **LangChain** | RAG pipeline orchestration |

---

## Prerequisites

- **Docker** version 20+
- **Docker Compose** version 2+ (bundled with Docker Desktop)
- **HuggingFace Access Token** (free) — [get one here](https://huggingface.co/settings/tokens)
- Minimum **8 GB RAM** (16 GB recommended)
- **10 GB free disk space** (for Docker images and HuggingFace models)

> No need to install Python, PostgreSQL, or Qdrant on your host machine. Everything runs inside Docker.

---

## Quick Start

### Step 1: Get the Code

Extract the provided `.zip` file or:

```bash
git clone <repository-url>
cd llm_document_qa
```

### Step 2: Create `.env`

```bash
cp .env.example .env
```

Open `.env` and set the values:

```env
# Django
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,web

# Database
DB_NAME=llm_project
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=document_chunks

# HuggingFace (LLM + Embeddings)
HF_TOKEN=hf_your_token_here
HF_MODEL_ID=HuggingFaceH4/zephyr-7b-beta
```

> ⚠️ **Important:** `.env` contains secrets. Never commit it to Git.

### Step 3: Start Services

```bash
docker-compose up -d
```

This will:
1. Build the Django image (first time: 5–15 min)
2. Start PostgreSQL and Qdrant
3. Run migrations automatically
4. Start Django on port 8000

### Step 4: Verify

```bash
docker-compose ps
```

Expected output:

```
NAME           IMAGE                      STATUS
llm_django     llm_document_qa-web        Up
llm_postgres   postgres:16                Up (healthy)
llm_qdrant     qdrant/qdrant:v1.15.4      Up (healthy)
```

### Step 5: Create a Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

Enter username, email, and password.

### Step 6: Access the System

| Service | URL |
|---------|-----|
| **Django Admin** | http://localhost:8000/admin/ |
| **Swagger UI** | http://localhost:8000/api/docs/ |
| **ReDoc** | http://localhost:8000/api/redoc/ |
| **Qdrant Dashboard** | http://localhost:6333/dashboard |

---

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Django secret key | — | Production: yes |
| `DEBUG` | Debug mode | `True` | No |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1,0.0.0.0,web` | No |
| `DB_NAME` | Database name | `llm_project` | No |
| `DB_USER` | Database user | `postgres` | No |
| `DB_PASSWORD` | Database password | `postgres` | No |
| `DB_HOST` | Database host | `db` | No |
| `DB_PORT` | Database port | `5432` | No |
| `QDRANT_HOST` | Qdrant hostname | `qdrant` | No |
| `QDRANT_PORT` | Qdrant port | `6333` | No |
| `QDRANT_COLLECTION` | Qdrant collection name | `document_chunks` | No |
| `HF_TOKEN` | HuggingFace token | — | **Yes** |
| `HF_MODEL_ID` | LLM model | `HuggingFaceH4/zephyr-7b-beta` | No |

---

## How to Use the System

### Step 1: Log into the Admin Panel

1. Go to `http://localhost:8000/admin/`
2. Log in with the superuser credentials

### Step 2: Upload a Document

1. From the left sidebar, click **"Documents"**
2. Click **"Add document"** (top-right)
3. Fill in:
   - **Title:** e.g., `Artificial Intelligence`
   - **File (docx):** upload a Word file
   - **Full text:** leave empty (auto-extracted from the file)
4. Click **Save**

After saving:
- Django automatically extracts text from the file
- The "Full text" field is populated
- `is_processed` is still `False` (not yet processed)

### Step 3: Process the Document (chunking + embedding)

1. In the document list, check the box next to the document
2. From the actions dropdown at the top, select **"Process selected documents (chunking + Qdrant)"**
3. Click **Go**

Behind the scenes:
- Text is split into ~500-character chunks
- Each chunk is converted to a 768-dim vector (LaBSE)
- Vectors are stored in Qdrant

> ⚠️ **First time:** The HuggingFace model (~1.8 GB) will be downloaded. It is cached in the `hf_cache` volume, so subsequent runs are fast.

After processing:
- `is_processed` = `True`
- Chunk count is shown in the "Chunk count" column
- Vectors are visible in the [Qdrant Dashboard](http://localhost:6333/dashboard)

### Step 4: Ask a Question

1. From the left sidebar, click **"Questions"**
2. Click **"Add question"** (top-right)
3. Fill in:
   - **Question text:** e.g., `What is artificial intelligence?`
   - **Document (optional):**
     - Leave empty → search **all documents**
     - Select one → search **only that document**
4. Click **Save**
5. Back in the question list, check the box next to the question
6. From the actions dropdown, select **"Ask selected questions to the LLM"**
7. Click **Go**

Behind the scenes:
1. The question is embedded
2. Qdrant finds the closest chunks (filtered by document if selected)
3. Chunks are sent to the LLM
4. The LLM generates an answer
5. Answer + sources are stored

After completion:
- The **"Answer"** field is populated
- The **"Sources"** field is filled with the used chunks
- Status changes to `answered`

### Step 5: View History

All questions and answers are stored at `http://localhost:8000/admin/qa/question/`. You can:
- Filter by document
- Filter by status
- Search in question and answer text

---

## API Documentation

### Base URL

```
http://localhost:8000/api/
```

### Authentication

Currently `AllowAny` (no auth). For production, add JWT.

### Interactive Docs

- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/

### Endpoints Summary

#### 📄 Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/documents/` | List documents |
| `POST` | `/api/documents/` | Create a document |
| `GET` | `/api/documents/{id}/` | Retrieve document + chunks |
| `PATCH` | `/api/documents/{id}/` | Partial update |
| `DELETE` | `/api/documents/{id}/` | Delete |
| `POST` | `/api/documents/{id}/process/` | Process (chunking + Qdrant) |

**Create with text:**

```bash
curl -X POST http://localhost:8000/api/documents/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Sample", "full_text": "Content..."}'
```

**Create with file:**

```bash
curl -X POST http://localhost:8000/api/documents/ \
  -F "title=Sample" \
  -F "file=@sample.docx"
```

#### 🧩 Chunks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/chunks/` | List all |
| `GET` | `/api/chunks/?document_id=3` | Filter by document |

#### 💬 Questions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/questions/` | History |
| `DELETE` | `/api/questions/{id}/` | Delete |
| `POST` | `/api/questions/ask/` | **Ask a question (RAG)** |

**Ask a question:**

```bash
curl -X POST http://localhost:8000/api/questions/ask/ \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is AI?",
    "k": 4,
    "document_id": null,
    "save": true
  }'
```

Parameters:
- `text` (required) — question text
- `k` (optional, default 4) — number of chunks to retrieve (1–10)
- `document_id` (optional) — restrict search to one document
- `save` (optional, default true) — save to history

**Response:**

```json
{
  "question_id": 5,
  "text": "What is AI?",
  "answer": "Artificial intelligence is...",
  "status": "answered",
  "sources": [
    {
      "chunk_id": 12,
      "document_id": 3,
      "document_title": "AI Basics",
      "chunk_index": 0,
      "content": "..."
    }
  ]
}
```

#### 🔍 Semantic Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/search/?q={query}&k={k}` | Search without LLM |

```bash
curl "http://localhost:8000/api/search/?q=artificial%20intelligence&k=3"
```

> **Score:** Cosine similarity. Range [0, 1]. Higher = more similar.

---

## Project Structure

```
llm_document_qa/
│
├── config/                          # Django project settings
│   ├── settings.py                  # Reads from .env
│   ├── urls.py                      # Root URLs
│   └── ...
│
├── documents/                       # Document management app
│   ├── models.py                    # Document, DocumentChunk
│   ├── serializers.py               # DRF serializers
│   ├── views.py                     # DocumentViewSet
│   ├── urls.py                      # Router
│   ├── admin.py                     # Django admin
│   ├── utils.py                     # Text extraction + chunking
│   └── embeddings.py                # Qdrant + HuggingFace
│
├── qa/                              # Question-Answering app
│   ├── models.py                    # Question
│   ├── serializers.py               # DRF serializers
│   ├── views.py                     # QuestionViewSet, SearchView
│   ├── urls.py                      # Router
│   ├── admin.py                     # Django admin
│   └── services.py                  # RAG chain + LLM
│
├── sample_data/                     # Sample documents
├── docs/                            # Screenshots and docs
├── media/                           # Uploaded files
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── requirements.txt
├── .env.example
└── README.md
```

---

## Technical Decisions

### Why Django + DRF?
Django Admin is production-ready, DRF provides clean REST APIs, mature ecosystem.

### Why Qdrant over FAISS?
Qdrant is a standalone service with native metadata filtering, better concurrency, and excellent Docker integration.

### Why LaBSE for embeddings?
Free, offline, multilingual (Persian, English, 50+ languages), and good quality for RAG.

### Why RAG instead of fine-tuning?
No training data needed, always up-to-date, source attribution, lower cost, instant updates.

### Why 500-char chunks?
Optimal for embedding models, large enough for meaningful context, small for precise retrieval, with 50-char overlap to prevent information loss at boundaries.

### Why cosine similarity?
The embedding model normalizes vectors; for normalized vectors, cosine distance is fast and reliable.

---

## Common Commands

### Docker

```bash
# Start
docker-compose up -d

# Stop (data preserved)
docker-compose down

# Stop and delete all data
docker-compose down -v

# Logs
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f qdrant

# Restart a service
docker-compose restart web

# Open a shell in the container
docker-compose exec web bash
```

### Django Management

```bash
# Migrations
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Superuser
docker-compose exec web python manage.py createsuperuser

# Django shell
docker-compose exec web python manage.py shell

# Collect static
docker-compose exec web python manage.py collectstatic
```

---

## Troubleshooting

### `port is already allocated`

The port is in use. Remove old containers:

```bash
docker ps -a
docker rm -f <container_id>
```

Or change the port in `docker-compose.yml`.

### `Connection refused` to PostgreSQL or Qdrant

- Ensure `DB_HOST=db` and `QDRANT_HOST=qdrant` (not `localhost`)
- Run `docker-compose ps` and check that all services are `Up (healthy)`

### `ModuleNotFoundError` in container

`requirements.txt` was updated but the image was not rebuilt:

```bash
docker-compose build --no-cache web
docker-compose up -d
```

### HuggingFace model re-downloads every time

The `hf_cache` volume is missing. Check `docker-compose.yml`:

```yaml
volumes:
  - hf_cache:/root/.cache/huggingface
```

### `model_not_supported` from HuggingFace

The model is not available on Inference API. Use another model:

```env
HF_MODEL_ID=HuggingFaceH4/zephyr-7b-beta
```

### `429 Too Many Requests`

Daily quota exceeded. Wait 24 hours or switch models.

### First build is very slow

Normal. `torch` and `transformers` are large. To speed up, use CPU-only torch:

```dockerfile
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Out of disk space

```bash
docker system prune -a
docker volume prune
```

---

## Limitations

- **No authentication** — API is open. Add JWT for production
- **No rate limiting**
- **Free model quotas** — daily limits
- **No streaming** — responses returned at once
- **No re-ranking** — top-k from Qdrant directly
- **No conversation memory** — each question is independent
- **`DEBUG=True` by default** — set `DEBUG=False` and use a proper web server (Nginx + Gunicorn) for production

---

## Future Improvements

- 🔐 JWT authentication
- 📡 Streaming responses (SSE)
- 🔁 Re-ranking with a cross-encoder
- 💬 Conversation memory (multi-turn)
- 📄 Support for PDF, HTML, Markdown
- ⚡ Async processing with Celery
- 🎯 pgvector instead of Qdrant
- 🧪 Unit + integration tests with pytest-django