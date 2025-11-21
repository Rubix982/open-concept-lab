# Deployment Guide

## Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 16GB RAM minimum
- 50GB disk space

## Production Deployment

### 1. Environment Configuration
```bash
cp .env.example .env
# Edit .env with production values
```

### 2. SSL/TLS Setup
```bash
# Generate certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./certs/key.pem -out ./certs/cert.pem
```

### 3. Start Services
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Initialize Database
```bash
make migrate
```

### 5. Verify Health
```bash
curl http://localhost:8080/health
```

## Scaling

### Horizontal Scaling
Add more workers:
```yaml
services:
  app:
    deploy:
      replicas: 3
```

### Vertical Scaling
Increase resources:
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

## Monitoring

### Access Dashboards
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Temporal UI**: http://localhost:8088

### Key Metrics
- Query latency (p95 < 500ms)
- Ingestion throughput (> 50 chunks/min)
- Error rate (< 1%)

## Backup & Recovery

### Backup
```bash
make backup
```

### Restore
```bash
make restore BACKUP_FILE=backup-2024-01-01.tar.gz
```

## Troubleshooting

### High Memory Usage
```bash
# Check container stats
docker stats

# Restart ChromaDB
docker-compose restart vector-db
```

### Slow Queries
```bash
# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=persistent_memory_query_duration_seconds

# Rebuild vector index
make rebuild-index
```
