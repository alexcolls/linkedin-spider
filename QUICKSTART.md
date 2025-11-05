# 🚀 LinkedIn Spider - Quick Start Guide

## What Was Built

A **production-ready distributed LinkedIn scraping system** with Docker and Kubernetes support for running **1,000+ concurrent worker pods**.

### Key Features ✨

- 🐳 **Containerized** with multi-stage Docker build
- ☸️ **Kubernetes-ready** with complete manifests
- 💾 **PostgreSQL** with automatic URL deduplication
- 📨 **Redis queue** for work distribution
- 🔐 **Session management** with shared LinkedIn cookies
- ⚙️ **1,000 workers** default (scalable)
- 🛡️ **Production security** (non-root, network policies)

---

## 📁 Project Structure

```
linkedin-spider/
├── Dockerfile                      # Multi-stage container image
├── docker-compose.yml             # Local development setup
├── k8s/                          # Kubernetes manifests
│   ├── 00-namespace.yaml
│   ├── 01-configmap.yaml
│   ├── 02-secret-template.yaml
│   ├── 10-postgres-statefulset.yaml
│   ├── 11-redis.yaml
│   ├── 20-worker-deployment.yaml
│   └── 30-network-policy.yaml
├── scripts/                      # Management scripts
│   ├── setup-minikube.sh
│   ├── deploy.sh
│   ├── monitor.sh
│   ├── scale-workers.sh
│   ├── teardown.sh
│   └── test-deployment.sh
├── src/linkedin_spider/
│   ├── db/                      # Database layer
│   ├── queue/                   # Message queue
│   ├── core/worker.py           # Distributed worker
│   ├── utils/session.py         # Cookie management
│   └── cli/extract_cookies.py   # Cookie extraction wizard
├── README-K8S.md                # Detailed K8s guide
└── DISTRIBUTED-SUMMARY.md       # Implementation overview
```

---

## ⚡ Quick Start (5 Steps)

### 1. Build Docker Image

```bash
docker build -t linkedin-spider:latest .
```

### 2. Test Locally with Docker Compose

```bash
# Start infrastructure
docker-compose up -d postgres redis

# Start 5 workers for testing
docker-compose up --scale worker=5
```

### 3. Extract LinkedIn Cookies

```bash
# Run the interactive wizard
poetry run python -m linkedin_spider.cli.extract_cookies --k8s-secret

# This will:
# - Open a browser
# - Let you log in manually (2FA supported)
# - Extract cookies
# - Generate k8s/linkedin-cookies-secret.yaml
```

### 4. Deploy to Kubernetes

```bash
# Setup minikube (if needed)
./scripts/setup-minikube.sh

# Load Docker image
minikube image load linkedin-spider:latest

# Deploy everything
./scripts/deploy.sh

# This will deploy with 10 workers initially
```

### 5. Push URLs and Monitor

```bash
# Option A: Push URLs via Redis CLI
kubectl run -it --rm redis-client --image=redis:7-alpine -n linkedin-spider -- sh
redis-cli -h redis
ZADD linkedin:urls 0 "https://www.linkedin.com/in/example/"

# Option B: Push URLs via Python
cat > push_urls.py <<EOF
from linkedin_spider.queue import get_producer
producer = get_producer()
urls = ["https://www.linkedin.com/in/example1/", 
        "https://www.linkedin.com/in/example2/"]
producer.push_urls_batch(urls)
print(f"Pushed {len(urls)} URLs. Queue size: {producer.get_queue_size()}")
EOF
poetry run python push_urls.py

# Monitor everything
./scripts/monitor.sh
```

---

## 📊 Scaling

```bash
# Scale to 10 workers
./scripts/scale-workers.sh 10

# Scale to 100 workers
./scripts/scale-workers.sh 100

# Scale to 1,000 workers (requires significant resources!)
./scripts/scale-workers.sh 1000
```

---

## 🔍 Monitoring

### Check Status

```bash
# Overall monitoring
./scripts/monitor.sh

# Pod status
kubectl get pods -n linkedin-spider

# Worker logs
kubectl logs -f -n linkedin-spider -l app=linkedin-spider-worker --tail=20

# Database query
kubectl exec -it postgres-0 -n linkedin-spider -- psql -U postgres -d linkedin_spider
```

### SQL Queries

```sql
-- Total profiles
SELECT COUNT(*) FROM profiles;

-- Top companies
SELECT company, COUNT(*) FROM profiles GROUP BY company ORDER BY COUNT(*) DESC LIMIT 10;

-- Worker performance
SELECT worker_id, COUNT(*) FROM profiles GROUP BY worker_id LIMIT 20;

-- Recent scrapes
SELECT url, scraped_at FROM profiles ORDER BY scraped_at DESC LIMIT 10;
```

---

## 🧪 Testing

```bash
# Run deployment tests
./scripts/test-deployment.sh

# Expected output:
# ✅ Namespace exists
# ✅ PostgreSQL is running
# ✅ Redis is running
# ✅ Workers are deployed
# ✅ ConfigMap exists
# ✅ Services are accessible
```

---

## 🛑 Cleanup

```bash
# Remove everything
./scripts/teardown.sh

# Or remove just workers
kubectl scale deployment linkedin-spider-worker -n linkedin-spider --replicas=0

# Stop minikube
minikube stop -p linkedin-spider
```

---

## 📈 Performance

**With 1,000 workers:**
- Theoretical: 120,000 profiles/hour
- Realistic: 20,000-60,000 profiles/hour (depends on rate limits)

**Resource Requirements:**
- Per worker: 500m CPU, 1Gi RAM
- 1,000 workers: ~500 CPU cores, ~1TB RAM

---

## 🆘 Troubleshooting

### Workers Not Starting

```bash
# Check logs
kubectl logs -n linkedin-spider -l app=linkedin-spider-worker --tail=50

# Check events
kubectl get events -n linkedin-spider --sort-by='.lastTimestamp'

# Verify secrets
kubectl get secret linkedin-credentials -n linkedin-spider
```

### Database Issues

```bash
# Check PostgreSQL
kubectl logs postgres-0 -n linkedin-spider

# Test connection
kubectl exec -it postgres-0 -n linkedin-spider -- psql -U postgres -d linkedin_spider -c "SELECT 1;"
```

### Redis Queue Issues

```bash
# Check queue size
kubectl exec -it <redis-pod> -n linkedin-spider -- redis-cli ZCARD linkedin:urls

# Clear queue
kubectl exec -it <redis-pod> -n linkedin-spider -- redis-cli DEL linkedin:urls
```

---

## 📚 Documentation

- **[README-K8S.md](./README-K8S.md)** - Complete Kubernetes guide
- **[DISTRIBUTED-SUMMARY.md](./DISTRIBUTED-SUMMARY.md)** - Implementation details
- **[README.md](./README.md)** - Main project documentation

---

## 🎯 Next Steps

1. **Test with 10 workers** first
2. **Monitor for 30 minutes** to verify stability
3. **Gradually scale up**: 10 → 50 → 100 → 500 → 1,000
4. **Adjust delays** in `config.yaml` to avoid rate limits
5. **Set up monitoring** (Prometheus/Grafana) for production

---

## ⚠️ Important Notes

1. **Cookie Expiration**: Rotate every 7-14 days
2. **Rate Limits**: LinkedIn may block aggressive scraping
3. **Cost**: 1,000 workers = expensive in cloud (use spot instances)
4. **Legal**: Use responsibly and respect LinkedIn's ToS
5. **Testing**: Always test with small scale first!

---

## 🎉 Success Metrics

Your deployment is ready when:

- ✅ All pods are Running
- ✅ Database is accessible
- ✅ Redis queue is operational
- ✅ Workers are consuming URLs
- ✅ Profiles are being saved to database
- ✅ No error spikes in logs

---

**Built with ❤️ using Docker, Kubernetes, PostgreSQL, Redis, and Python**

*Happy Scraping! 🕷️*
