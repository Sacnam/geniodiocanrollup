# Genio Knowledge OS - Production Deployment Guide

Complete guide for deploying Genio to production.

## 📋 Pre-Deployment Checklist

### Infrastructure Requirements
- [ ] Server with 16GB+ RAM, 4+ CPU cores
- [ ] 100GB+ SSD storage
- [ ] Ubuntu 22.04 LTS or similar
- [ ] Docker 24+ and Docker Compose 2+
- [ ] Domain name with SSL certificate
- [ ] S3 bucket for backups (optional but recommended)

### Environment Variables
Create `.env.production`:

```bash
# Required
DATABASE_URL=postgresql://genio:secure_password@postgres:5432/genio
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
ELASTICSEARCH_URL=http://elasticsearch:9200
JWT_SECRET_KEY=your-super-secret-32-char-min-key

# AI Services
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Email
SENDGRID_API_KEY=SG-...
EMAIL_FROM=noreply@yourdomain.com

# OAuth (Optional)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...

# Backups
BACKUP_S3_BUCKET=your-backup-bucket
BACKUP_AWS_KEY=AKIA...
BACKUP_AWS_SECRET=...
BACKUP_ENCRYPTION_KEY=your-encryption-key

# Monitoring
GRAFANA_PASSWORD=secure-admin-password
SLACK_WEBHOOK=https://hooks.slack.com/...
```

## 🚀 Deployment Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Configure system limits for Elasticsearch
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

### 2. Application Deployment

```bash
# Clone repository
git clone https://github.com/your-org/genio-mvp.git
cd genio-mvp

# Copy environment file
cp .env.production .env

# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Start infrastructure first
docker-compose -f docker-compose.prod.yml up -d postgres redis qdrant elasticsearch

# Wait for services
sleep 30

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Verify
docker-compose -f docker-compose.prod.yml ps
curl -f http://localhost:8000/health
```

### 3. SSL/TLS Setup

```bash
# Install certbot
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### 4. Initial Data Setup

```bash
# Create admin user
docker-compose -f docker-compose.prod.yml run --rm backend python scripts/create_admin.py

# Set up Elasticsearch indices
docker-compose -f docker-compose.prod.yml run --rm backend python -c "
from app.services.search_service import search_service
import asyncio
asyncio.run(search_service.ensure_index('genio_articles'))
"

# Install default plugins
docker-compose -f docker-compose.prod.yml run --rm backend python -c "
# Install default plugins here
"
```

## 📊 Monitoring Setup

### Access Monitoring Tools
- **Grafana**: http://your-server:3000 (admin/password)
- **Flower (Celery)**: http://your-server:5555
- **Prometheus**: http://your-server:9090

### Key Metrics to Monitor
1. **API Response Time**: p50 < 100ms, p95 < 500ms
2. **Error Rate**: < 1%
3. **Database Connections**: < 80% of max
4. **Redis Memory**: < 80% of limit
5. **Elasticsearch Heap**: < 75%
6. **Disk Space**: Alert at < 20%

### Alert Rules
Create `alertmanager.yml`:
```yaml
global:
  slack_api_url: 'YOUR_SLACK_WEBHOOK'

route:
  receiver: 'slack-notifications'

receivers:
- name: 'slack-notifications'
  slack_configs:
  - channel: '#alerts'
    title: 'Genio Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

## 🔄 Backup Strategy

### Automated Daily Backups

Add to crontab:
```bash
# Edit crontab
crontab -e

# Add line
0 2 * * * /app/genio-mvp/scripts/backup.sh >> /var/log/genio-backup.log 2>&1
```

### Backup Retention
- Daily backups: 30 days
- Weekly backups: 12 weeks
- Monthly backups: 12 months

### Disaster Recovery

```bash
# Restore from backup
./scripts/restore.sh /backups/genio_backup_20260218_020000

# Verify restoration
curl -f http://localhost:8000/health
```

## 🔧 Maintenance

### Daily Tasks (Automated)
- Database vacuum and analyze
- Cleanup old logs and snapshots
- Redis memory optimization
- Elasticsearch segment merging

### Weekly Tasks
- Review error logs
- Check disk usage
- Verify backup integrity
- Update SSL certificates if needed

### Monthly Tasks
- Review and optimize slow queries
- Update dependencies
- Security patches
- Performance tuning

## 🔐 Security Hardening

### 1. Firewall Setup
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Fail2ban
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### 3. Docker Security
```bash
# Run Docker Bench for Security
docker run -it --net host --pid host --userns host --cap-add audit_control \
    -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
    -v /var/lib:/var/lib \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /usr/lib/systemd:/usr/lib/systemd \
    -v /etc:/etc --label docker_bench_security \
    docker/docker-bench-security
```

### 4. Secrets Management
Use Docker Secrets or external vault:
```bash
# Example with Docker Secrets
echo "your-secret" | docker secret create jwt_secret -
```

## 🚀 Scaling

### Horizontal Scaling

```yaml
# docker-compose.prod.yml
deploy:
  replicas: 5
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

### Database Scaling
- Set up read replicas
- Use connection pooling (PgBouncer)
- Partition large tables

### Search Scaling
- Elasticsearch cluster with 3+ nodes
- Index sharding strategy
- Dedicated master nodes

### Load Balancing
```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

## 📈 Performance Tuning

### Database
```sql
-- Add connection pooling
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
```

### Redis
```conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### Elasticsearch
```yaml
# elasticsearch.yml
indices.memory.index_buffer_size: 20%
thread_pool.search.queue_size: 2000
```

## 🆘 Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check connection pool
docker-compose exec postgres psql -U genio -c "SELECT count(*) FROM pg_stat_activity;"
```

**Elasticsearch Out of Memory**
```bash
# Check heap usage
curl localhost:9200/_nodes/stats/jvm?pretty

# Reduce heap size in docker-compose
# ES_JAVA_OPTS=-Xms1g -Xmx1g
```

**Celery Queue Backlog**
```bash
# Check queue depth
docker-compose exec redis redis-cli LLEN celery

# Add more workers
docker-compose up -d --scale worker=5
```

**High Disk Usage**
```bash
# Check what's using space
docker system df -v

# Clean up
docker system prune -a
```

## 📞 Support

### Health Checks
```bash
# Full system health
curl http://localhost:8000/health

# Database
docker-compose exec postgres pg_isready -U genio

# Redis
docker-compose exec redis redis-cli ping

# Elasticsearch
curl http://localhost:9200/_cluster/health
```

### Logs
```bash
# View all logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

## 📚 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Elasticsearch Production](https://www.elastic.co/guide/en/elasticsearch/reference/current/high-availability.html)
- [PostgreSQL Tuning](https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server)
- [Redis Persistence](https://redis.io/docs/manual/persistence/)

---

**Your Genio Knowledge OS is now production-ready! 🚀**
