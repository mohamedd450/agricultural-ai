# System Architecture | البنية التقنية

## Overview

The Agricultural AI Platform is a multi-tier microservices system built around a Graph-RAG (Graph Retrieval-Augmented Generation) engine. The architecture prioritises explainability, multilingual support, and production reliability.

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                          │
│         Web Browser (React + TypeScript)                 │
│    Arabic RTL ◄────────────────────► English LTR        │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS / WSS
┌───────────────────────▼─────────────────────────────────┐
│                  API Gateway Layer                       │
│              Nginx (Reverse Proxy)                       │
│         Rate limiting · SSL termination · Compression   │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│               Application Layer (FastAPI)                │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Auth Layer │  │  REST Routes │  │  WebSocket    │  │
│  │  JWT + Rate │  │  /analyze    │  │  /ws          │  │
│  │  Limiting   │  │  /voice      │  │  Real-time    │  │
│  └─────────────┘  │  /history    │  │  Updates      │  │
│                   │  /feedback   │  └───────────────┘  │
│                   └──────────────┘                       │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│            LangGraph Orchestrator (Multi-Agent)          │
│                                                          │
│  router → vision_agent → edgequake_agent                │
│         → voice_agent  → vector_rag_agent               │
│                        → fusion_agent                    │
│                        → decision_agent → END            │
└──┬────────┬───────────┬──────────────────────────────────┘
   │        │           │
   ▼        ▼           ▼
Vision   Graph-RAG   Vector-DB
Service  (EdgeQuake) (Qdrant)
   │        │           │
   └────────┴───────────┘
            │
     Fusion Layer
            │
       Redis Cache
            │
     Final Response
```

---

## Decision Router Logic

The Decision Router is the **critical brain** of the system. It selects the optimal response strategy based on confidence scores from each AI source:

```python
# Confidence thresholds
VISION_THRESHOLD = 0.85   # High-confidence image classification
GRAPH_RAG_THRESHOLD = 0.7 # Reliable graph reasoning

if has_image and vision_confidence > VISION_THRESHOLD:
    strategy = "vision_primary"    # Trust image classification
elif graph_rag_confidence > GRAPH_RAG_THRESHOLD:
    strategy = "graph_primary"     # Trust knowledge graph reasoning
else:
    strategy = "fusion"            # Combine all sources
```

### Routing Strategies

| Strategy | Trigger | Primary Source |
|----------|---------|----------------|
| `vision_primary` | Image present AND vision conf > 0.85 | Vision AI |
| `graph_primary` | Graph-RAG conf > 0.7 | EdgeQuake Graph-RAG |
| `fusion` | No single source above threshold | All sources combined |

---

## Fusion Algorithm

When multiple sources are active, results are merged using weighted scoring:

```
fusion_score = (vision_conf × 0.3) + (graph_rag_conf × 0.4) + (vector_db_conf × 0.3)
```

**Weights rationale:**
- **Graph-RAG (0.4)**: Highest weight – multi-hop reasoning provides most reliable agricultural knowledge
- **Vision (0.3)**: Second – direct image evidence
- **Vector DB (0.3)**: Semantic similarity backup

---

## Component Details

### 1. Vision Service (`vision_service.py`)
- Model: EfficientNet-B0 (PyTorch)
- Input: Raw image bytes (JPG/PNG/WebP)
- Output: `{class, confidence, all_predictions}`
- Feature: Grad-CAM heatmap generation for explainability

### 2. Voice Service (`voice_service.py`)
- STT: OpenAI Whisper (supports Arabic natively)
- TTS: gTTS (Google Text-to-Speech)
- Languages: Arabic, English
- Output: Transcription text + audio MP3 bytes

### 3. Graph-RAG Service (`graph_rag_service.py`)
- Engine: EdgeQuake (Rust-based, high-performance)
- Reasoning: Multi-hop path traversal
- Output: `{answer, confidence, graph_paths, reasoning_steps}`
- Example: `yellow_leaves → nitrogen_deficiency → urea_fertilizer`

### 4. Vector DB Service (`vector_db_service.py`)
- Database: Qdrant
- Embeddings: sentence-transformers (384-dim)
- Search: Cosine similarity
- Collection: `agricultural_embeddings`

### 5. LLM Service (`llm_service.py`)
- API: OpenAI-compatible (gpt-4o-mini default)
- Fallback: Template-based responses when API unavailable
- Prompts: Bilingual templates for diagnosis and treatment

### 6. Cache Service (`cache_service.py`)
- Backend: Redis
- Strategy: TTL-based with hash keys
- Hit rate monitoring via Prometheus

### 7. Decision Router (`decision_router.py`)
- Stateless confidence-based routing
- Thresholds configurable via environment variables

### 8. Fusion Service (`fusion_service.py`)
- Weighted multi-source merging
- Graph path deduplication
- Bilingual explanation generation

---

## LangGraph Workflow

```
START
  └── router_node
        ├── [input_type=image] → vision_node
        │                         └── edgequake_node
        ├── [input_type=voice] → voice_node
        │                         └── edgequake_node
        └── [input_type=text] → edgequake_node
                                   └── vector_rag_node
                                         └── fusion_node
                                               └── decision_node
                                                     └── END
```

---

## Data Pipeline

```
PDFs (ICAR, FAO, Arabic Books)
        ↓
OCR + Extraction (pypdf + pytesseract)
        ↓
Text Cleaning (TextCleaner)
  - Arabic diacritic removal
  - Alef variant normalization
  - URL/email stripping
        ↓
Semantic Chunking (512 chars, 50 overlap)
        ↓
Embeddings (sentence-transformers, 384-dim)
        ↓
        ├── Qdrant (vector similarity search)
        └── Neo4j (knowledge graph)
              ├── Entity extraction (NER)
              └── Relationship extraction
```

---

## Database Schemas

### Neo4j Node Labels
| Label | Properties |
|-------|-----------|
| `Disease` | name, description_ar, description_en, severity |
| `Symptom` | name, visible_on, description |
| `Crop` | name, scientific_name, family |
| `Fertilizer` | name, npk_ratio, application_method |
| `WeatherCondition` | type, temperature_range, humidity_range |

### Neo4j Relationship Types
| Relationship | From → To | Properties |
|-------------|-----------|-----------|
| `CAUSES` | Disease → Symptom | confidence |
| `TREATED_BY` | Disease → Fertilizer | dosage, timing |
| `WORSENED_BY` | Disease → WeatherCondition | - |
| `AFFECTS` | Disease → Crop | frequency |
| `TRIGGERED_BY` | Disease → WeatherCondition | - |

### Qdrant Collection
- **Collection**: `agricultural_embeddings`
- **Vector size**: 384 (sentence-transformers/all-MiniLM-L6-v2)
- **Distance**: Cosine
- **Payload**: `{text, metadata: {source, page, language, chunk_index}}`

---

## Security Architecture

| Layer | Mechanism |
|-------|----------|
| **Authentication** | JWT Bearer tokens (HS256, 30min expiry) |
| **Rate Limiting** | 100 req/min per user (Redis-backed) |
| **Input Validation** | Pydantic v2 strict mode + custom validators |
| **Sanitization** | HTML/SQL injection prevention |
| **CORS** | Allowlist-based origin control |
| **Headers** | Security headers via Nginx (HSTS, CSP, X-Frame-Options) |

---

## Observability

| Component | Tool | Endpoint/Port |
|-----------|------|--------------|
| **Metrics** | Prometheus | `:8000/metrics` |
| **Dashboards** | Grafana | `:3001` |
| **Logs** | Structured JSON | stdout |
| **Health** | FastAPI | `/api/v1/health` |

### Key Metrics
- `http_requests_total` – Request count by method/endpoint/status
- `http_request_duration_seconds` – Latency histogram
- `vision_inference_duration_seconds` – EfficientNet inference time
- `graph_rag_query_duration_seconds` – EdgeQuake query time
- `cache_hits_total` / `cache_misses_total` – Redis hit rate
- `websocket_connections_active` – Active WS connections
