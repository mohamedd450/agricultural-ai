# Deployment Guide | دليل النشر

## Prerequisites | المتطلبات

- Docker Engine 24+
- Docker Compose 2.20+
- 8 GB RAM minimum (16 GB recommended for production)
- 20 GB free disk space
- Domain name (for production with SSL)

---

## Development Deployment

### 1. Clone repository
```bash
git clone https://github.com/mohamedd450/agricultural-ai.git
cd agricultural-ai
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your values
nano .env
```

### 3. Start all services
```bash
docker compose up -d
```

### 4. Verify services
```bash
docker compose ps
curl http://localhost:8000/api/v1/health
```

### Available services (development)
| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Neo4j Browser | http://localhost:7474 |
| Qdrant Dashboard | http://localhost:6333/dashboard |
| Redis | localhost:6379 |

---

## Production Deployment

### 1. Configure production environment
```bash
cp .env.example .env
```

Required production values:
```bash
# Security
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>

# Database passwords (strong, unique)
NEO4J_PASSWORD=<strong-password>

# LLM
OPENAI_API_KEY=sk-...

# CORS (your frontend domain)
CORS_ORIGINS=["https://yourdomain.com"]

# Debug off
DEBUG=false
```

### 2. SSL/TLS Configuration

Edit `nginx.conf` to add your SSL certificates:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
}
```

Mount certificates in `docker-compose.prod.yml`:
```yaml
nginx:
  volumes:
    - ./ssl:/etc/nginx/ssl:ro
```

### 3. Start production stack
```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4. Initialize databases
```bash
# Run Neo4j graph schema migrations
docker compose exec backend python -m app.migrations.init_graph

# Verify Qdrant collection exists
curl http://localhost:6333/collections
```

### 5. Ingest data (optional)
```bash
# Place PDF files in ./data/pdfs/
docker compose run --rm data-pipeline /data/pdfs --language ar
```

---

## Monitoring Setup

### Prometheus
Metrics are scraped automatically from the backend at `:8000/metrics`.

Edit `prometheus.yml` to add additional targets:
```yaml
scrape_configs:
  - job_name: "agricultural-ai-backend"
    static_configs:
      - targets: ["backend:8000"]
```

### Grafana
1. Access Grafana at http://localhost:3001 (admin/admin)
2. Add Prometheus datasource: http://prometheus:9090
3. Import dashboard from `grafana-dashboard.json`:
   - Click **+** → **Import**
   - Upload `grafana-dashboard.json`
   - Select Prometheus datasource

---

## Scaling

### Horizontal scaling (backend)
```yaml
# docker-compose.prod.yml
backend:
  deploy:
    replicas: 3
```

### Database scaling
- **Neo4j**: Use Neo4j Cluster (Enterprise) for high availability
- **Qdrant**: Use Qdrant distributed mode for large collections
- **Redis**: Use Redis Sentinel or Redis Cluster

---

## Backup Procedures

### Neo4j backup
```bash
docker compose exec neo4j neo4j-admin database dump neo4j --to-path=/backups/
```

### Qdrant backup
```bash
# Use Qdrant snapshots API
curl -X POST http://localhost:6333/collections/agricultural_embeddings/snapshots
```

### Redis backup
```bash
docker compose exec redis redis-cli BGSAVE
docker cp agricultural-ai-redis-1:/data/dump.rdb ./backups/redis-$(date +%Y%m%d).rdb
```

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker compose logs backend -f

# Common issues:
# 1. Neo4j not ready → docker-entrypoint.sh waits, but increase WAIT_SECONDS in .env
# 2. Port conflict → change ports in docker-compose.yml
# 3. Missing .env → cp .env.example .env
```

### Neo4j connection refused
```bash
# Check Neo4j is healthy
docker compose ps neo4j
docker compose logs neo4j

# Reset Neo4j password
docker compose exec neo4j neo4j-admin dbms set-initial-password newpassword
```

### Frontend blank page
```bash
# Check API URL in frontend/.env
REACT_APP_API_URL=http://localhost:8000/api/v1

# Rebuild frontend
docker compose build frontend
docker compose up -d frontend
```

### High memory usage
```bash
# Limit Whisper model size in .env
WHISPER_MODEL_SIZE=tiny  # instead of base/small/medium

# Check container memory
docker stats
```
