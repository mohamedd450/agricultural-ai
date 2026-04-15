# 🌿 Agricultural AI Platform

<div align="center">

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue.svg)](https://typescriptlang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**منصة زراعية ذكية متعددة الوسائط مع Graph-RAG**  
*A Production-Ready Multimodal AI Platform for Smart Agriculture*

[Architecture](ARCHITECTURE.md) · [Deployment](DEPLOYMENT.md) · [Development](DEVELOPMENT.md)

</div>

---

## 📋 Overview | نبذة عامة

The **Agricultural AI Platform** is a production-ready system that combines computer vision, voice AI, and knowledge-graph reasoning to diagnose crop diseases, nutrient deficiencies, and pest problems in multiple languages (Arabic & English).

**المنصة الزراعية الذكية** نظام متكامل جاهز للإنتاج يجمع بين رؤية الحاسوب والذكاء الصوتي والاستدلال على مخططات المعرفة لتشخيص أمراض المحاصيل ونقص المغذيات ومشاكل الآفات بلغات متعددة.

---

## ✨ Features | الميزات

| Feature | Description |
|---------|-------------|
| 🖼️ **Vision AI** | EfficientNet crop disease classification with Grad-CAM heatmaps |
| 🎤 **Voice AI** | Whisper STT + gTTS TTS with Arabic & English support |
| 🧠 **Graph-RAG** | EdgeQuake multi-hop knowledge graph reasoning |
| 🔀 **Smart Routing** | Confidence-based decision router (vision > 0.85, graph > 0.7) |
| 🔗 **Fusion Engine** | Weighted fusion: vision×0.3 + graph-rag×0.4 + vector×0.3 |
| 🌍 **Multilingual** | Full Arabic (RTL) and English support throughout |
| ⚡ **Performance** | Redis caching, async FastAPI, batch embeddings |
| 🔐 **Security** | JWT auth, rate limiting, input sanitization |
| 📊 **Monitoring** | Prometheus metrics, Grafana dashboards, structured logging |
| 🐳 **Production** | Docker Compose with health checks and restart policies |

---

## 🚀 Quick Start | بدء سريع

### Prerequisites
- Docker & Docker Compose
- Git

### 1. Clone & Configure

```bash
git clone https://github.com/mohamedd450/agricultural-ai.git
cd agricultural-ai
cp .env.example .env          # Edit with your API keys
```

### 2. Start Development Stack

```bash
docker compose up -d
```

Services started:
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### 3. Run Data Pipeline (optional)

```bash
docker compose run --rm data-pipeline /data/pdfs
```

---

## 🏗️ Architecture | البنية التقنية

```
User (Text / Image / Voice)
         ↓
   API Gateway (FastAPI + Nginx)
         ↓
   Auth (JWT + Rate Limiting)
         ↓
   LangGraph Orchestrator
         ↓
   Decision Router  ◄──── Confidence Thresholds
    ↙      ↓      ↘
Vision  Graph-RAG  Vector-DB
    ↘      ↓      ↙
      Fusion Layer
         ↓
   Redis Cache
         ↓
   Final Response (Text + Graph + Voice)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full details.

---

## 🧰 Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, Pydantic v2 |
| **Orchestration** | LangGraph, LangChain |
| **Graph-RAG** | EdgeQuake (Rust-based) |
| **Vision** | PyTorch, EfficientNet |
| **Voice** | OpenAI Whisper, gTTS |
| **Vector DB** | Qdrant |
| **Graph DB** | Neo4j |
| **Cache** | Redis |
| **Frontend** | React 18, TypeScript, Sigma.js |
| **i18n** | react-i18next (Arabic + English) |
| **Infra** | Docker, Nginx, Prometheus, Grafana |

---

## 📁 Project Structure

```
agricultural-ai/
├── backend/            # FastAPI application
│   └── app/
│       ├── api/        # Routes & WebSocket
│       ├── services/   # 8 AI services
│       ├── orchestrators/ # LangGraph workflow
│       ├── database/   # Neo4j client
│       ├── models/     # Pydantic models
│       └── utils/      # Logging, metrics, exceptions
├── frontend/           # React TypeScript app
│   └── src/
│       ├── components/ # UI components
│       ├── pages/      # Route pages
│       ├── hooks/      # Custom hooks
│       └── i18n/       # AR/EN translations
├── data-pipeline/      # Ingestion pipeline
│   ├── ingestion/      # PDF processor, text cleaner
│   ├── processing/     # Chunker, embeddings, graph extractor
│   ├── storage/        # Qdrant & Neo4j loaders
│   └── scripts/        # CLI scripts
└── infrastructure/     # Prometheus, Grafana configs
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze` | Analyze image + text query |
| `POST` | `/api/v1/voice` | Voice input/output |
| `GET`  | `/api/v1/history` | Analysis history |
| `POST` | `/api/v1/feedback` | Submit feedback |
| `GET`  | `/api/v1/health` | Health check |
| `WS`   | `/ws` | Real-time WebSocket updates |

---

## 📖 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) – System design & component details
- [DEPLOYMENT.md](DEPLOYMENT.md) – Production deployment guide
- [DEVELOPMENT.md](DEVELOPMENT.md) – Local dev setup & contributing

---

## 📄 License

MIT License – see [LICENSE](LICENSE) for details.
