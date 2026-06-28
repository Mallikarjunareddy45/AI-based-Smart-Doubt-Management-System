# Smart AI Question Routing System for Large Online Courses

DoubtAssist is an enterprise-grade, AI-powered question routing and real-time chat platform designed for large online courses (thousands of concurrent students). It automatically clusters semantically similar doubts, calculates urgency priority indexes, and dynamically assigns tasks to course assistants using a load-balanced matching queue.

---

## 🛠️ Tech Stack & Architecture

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Framer Motion, Axios, React Query, React Router.
- **Backend**: FastAPI (Python 3.10), PostgreSQL (with `pgvector` index extensions), Redis (Cache & WebSockets PubSub), Celery (Background Worker threads), SQLAlchemy 2.0, Pydantic v2.
- **AI Core**: NLP Sentence Transformers (`all-MiniLM-L6-v2`), Scikit-learn DBSCAN (density-based clustering), HNSW Cosine Indexing.
- **Orchestration**: Docker Compose, Nginx.

---

## 🚀 Quick Start (Docker Orchestrated)

Ensure you have **Docker** and **Docker Compose** installed.

1.  **Clone the project** to your local workspace directory.
2.  **Spin up all services**:
    ```bash
    docker-compose up --build
    ```
    This command will automatically download and start:
    - **PostgreSQL** with pgvector on port `5432`
    - **Redis Cache & Broker** on port `6379`
    - **FastAPI Application Server** on port `8000` (serving REST APIs and WebSockets)
    - **Celery Worker Pool** for background NLP processing
    - **Nginx Web Server** on port `80` (serving compiled React SPA assets and proxying requests)

3.  **Access the applications**:
    - **UI Panel**: Navigate to [http://localhost](http://localhost) in your browser.
    - **Interactive API Swagger Docs**: Navigate to [http://localhost:8000/docs](http://localhost:8000/docs).

---

## ⚙️ Local Development Setup (Manual)

If you prefer to run services manually without Docker wrappers:

### 1. PostgreSQL & Redis
- Ensure you have **PostgreSQL 14+** running locally with the **pgvector** extension active:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```
- Ensure you have a local **Redis** instance running on `localhost:6379`.

### 2. Backend Server Setup
Navigate to the `backend/` directory:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```
Run database migrations using Alembic:
```bash
alembic upgrade head
```
Start the FastAPI server:
```bash
uvicorn app.main:app --reload --port 8000
```
Start the Celery worker pool in a separate terminal:
```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=info --pool=solo
```

### 3. Frontend UI Setup
Navigate to the `frontend/` directory:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🔑 Core Configuration (.env)

Adjust local secrets and connection URLs inside `backend/.env` (see template inside `backend/.env.example`):

| Key | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://postgres:postgres@db:5432/ai_doubt_system` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `SECRET_KEY` | JWT encryption passphrase | `SUPER_SECRET_SECURITY_PASSPHRASE_CHANGE_IN_PRODUCTION` |
| `AI_SIMILARITY_THRESHOLD` | Cosine threshold (0.0 to 1.0) | `0.82` |

---

## 🧪 Running the Test Suite

Execute unit tests and AI logic verification cases within the `backend/` space:
```bash
cd backend
pytest -v
```
This runs:
- **`test_auth.py`**: checks student registration, token issuance, and guard interceptions.
- **`test_ai_logic.py`**: asserts cosine similarities and DBSCAN vector grouping accuracy.
