# QABuddy.ai

Self-hosted Hybrid RAG chatbot for QA engineers. Answers questions grounded in your Selenium/Playwright frameworks, test cases, JIRA tickets, PRDs, and Jenkins logs — with citations.

## Quick Start

### 1. Configure credentials
```bash
cp .env.example .env
# Edit .env — add JIRA_API_TOKEN, ANTHROPIC_API_KEY
```

### 2. Add your data
Place files in the appropriate `data/` folders:
- `data/01_selenium_framework/` — clone your Selenium repo here
- `data/02_playwright_framework/` — clone your Playwright repo here
- `data/03_test_cases/` — put CSV/XLSX test case files here
- `data/05_company_docs/` — PDF and MD docs
- `data/07_meeting_notes/` — text transcripts
- `data/08_lucid_charts/` — exported text
- `data/09_prd_srs_brd_frd/` — PDF specs
- `data/10_jenkins_logs/` — .log files

JIRA tickets are fetched live from `config/jql_queries.yaml`.

### 3. Start with Docker
```bash
docker compose up --build
```

### 4. Run ingestion
```bash
# Ingest everything
docker exec qabuddy-api python -m ingestion.pipeline --source all

# Ingest one source
docker exec qabuddy-api python -m ingestion.pipeline --source 01_selenium_framework

# Ingest JIRA only
docker exec qabuddy-api python -m ingestion.pipeline --source 04_jira_tickets
```

### 5. Open the chat UI
http://localhost:8501

### 6. API
http://localhost:8000/docs

## Running locally (no Docker)
```bash
pip install -r requirements.txt

# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant:v1.11.3

# Ingest
python -m ingestion.pipeline --source all

# Start API
uvicorn api.main:app --port 8000

# Start UI
streamlit run ui/app.py
```

## Architecture
- **Embedding:** BAAI/bge-large-en-v1.5 (1024-dim, local)
- **Vector DB:** Qdrant (hybrid dense+sparse, RRF fusion)
- **LLM:** Claude API (default) or Ollama (set LLM_PROVIDER=ollama)
- **API:** FastAPI
- **UI:** Streamlit

## Phase 2 (planned)
- Hourly auto-ingestion with incremental updates
- Figma design ingestion via Figma REST API + OCR
