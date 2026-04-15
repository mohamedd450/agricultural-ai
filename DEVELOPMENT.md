# Development Guide | دليل التطوير

## Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### 1. Clone and setup
```bash
git clone https://github.com/mohamedd450/agricultural-ai.git
cd agricultural-ai
```

### 2. Backend setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with local values
```

### 3. Start infrastructure (databases only)
```bash
# From repo root
docker compose up -d neo4j redis qdrant
```

### 4. Run backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Frontend setup
```bash
cd frontend
npm install
cp .env.example .env
npm start
```

---

## Running Tests

### Backend tests
```bash
cd backend
pytest app/tests/ -v

# With coverage
pytest app/tests/ -v --cov=app --cov-report=html

# Single test file
pytest app/tests/test_fusion.py -v

# Specific test
pytest app/tests/test_fusion.py::TestConfidenceWeighting -v
```

### Data pipeline tests
```bash
cd data-pipeline
pip install -r requirements.txt
pytest scripts/test_pipeline.py -v
```

---

## Code Style Guide

### Python (Backend)
- Follow PEP 8
- Use type hints everywhere (`from __future__ import annotations`)
- Docstrings for all public classes and methods
- Async functions for I/O operations
- Custom exceptions from `app/utils/exceptions.py`

```python
# Good
async def analyze_image(self, image_data: bytes) -> dict:
    """Analyze a plant image for disease detection.
    
    Returns
    -------
    dict
        ``{"class": str, "confidence": float}``
    """
    ...

# Bad
async def analyze(self, data):
    ...
```

### TypeScript (Frontend)
- Strict mode enabled in tsconfig.json
- Interfaces over types for object shapes
- Named exports over default where possible
- `useCallback`/`useMemo` for expensive operations

```typescript
// Good
export interface DiagnosisResult {
  diagnosis: string;
  confidence: number;
  graph_paths: string[];
}

// Bad
export type DiagnosisResult = {
  diagnosis: any;
}
```

---

## Project Structure Overview

```
agricultural-ai/
├── backend/app/
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Pydantic Settings
│   ├── security.py          # JWT + rate limiting
│   ├── dependencies.py      # Dependency injection
│   ├── api/
│   │   ├── routes.py        # REST endpoints
│   │   └── websocket.py     # WebSocket handler
│   ├── services/
│   │   ├── vision_service.py
│   │   ├── voice_service.py
│   │   ├── graph_rag_service.py
│   │   ├── vector_db_service.py
│   │   ├── decision_router.py
│   │   ├── fusion_service.py
│   │   ├── cache_service.py
│   │   └── llm_service.py
│   ├── orchestrators/
│   │   ├── langgraph_orchestrator.py
│   │   └── workflow_nodes.py
│   ├── database/
│   │   ├── neo4j_client.py
│   │   ├── schemas.py
│   │   └── queries.py
│   ├── models/
│   │   ├── request_models.py
│   │   ├── response_models.py
│   │   └── graph_models.py
│   └── utils/
│       ├── logger.py
│       ├── validators.py
│       ├── exceptions.py
│       ├── metrics.py
│       └── prompts.py
├── frontend/src/
│   ├── components/          # Reusable UI components
│   ├── pages/               # Route pages
│   ├── services/            # API/WebSocket clients
│   ├── hooks/               # Custom React hooks
│   ├── i18n/                # AR/EN translations
│   └── types/               # TypeScript definitions
└── data-pipeline/
    ├── ingestion/           # PDF & text processing
    ├── processing/          # Chunking & embeddings
    ├── storage/             # DB loaders
    └── scripts/             # CLI tools
```

---

## Adding a New Service

1. Create `backend/app/services/my_service.py`
2. Add to `backend/app/dependencies.py`:
   ```python
   @lru_cache()
   def get_my_service() -> MyService:
       return MyService()
   ```
3. Inject in routes:
   ```python
   @router.post("/my-endpoint")
   async def my_endpoint(
       service: MyService = Depends(get_my_service)
   ):
       ...
   ```
4. Add tests in `backend/app/tests/test_my_service.py`

---

## API Development Guidelines

### Request validation
Use Pydantic models from `app/models/request_models.py`:
```python
class MyRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    language: str = Field(default="ar", pattern="^(ar|en)$")
```

### Error handling
Raise custom exceptions from `app/utils/exceptions.py`:
```python
raise InvalidInputError(
    message="Image too large",
    details={"max_size_mb": 10, "provided_mb": 15}
)
```

### Logging
Use structured logger:
```python
from app.utils.logger import get_logger
logger = get_logger(__name__)
logger.info("Processing request", extra={"session_id": session_id})
```

---

## Frontend Development

### Adding a new component
1. Create `frontend/src/components/MyComponent.tsx`
2. Add Arabic translations to `frontend/src/i18n/ar.json`
3. Add English translations to `frontend/src/i18n/en.json`
4. Use `useTranslation()` hook:
   ```tsx
   const { t } = useTranslation();
   return <h1>{t("myComponent.title")}</h1>;
   ```

### RTL Support
- Use `[dir="rtl"]` CSS selectors for RTL-specific styles
- Test with both `lang="ar"` and `lang="en"` settings
- The app automatically sets `document.dir` based on language

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes following the code style guide
4. Write tests for new functionality
5. Run the full test suite: `pytest app/tests/ -v`
6. Submit a Pull Request

### Commit message format
```
type(scope): short description

Examples:
feat(vision): add multi-image support
fix(router): handle missing confidence scores
docs(api): update endpoint documentation
test(fusion): add edge case tests
```
