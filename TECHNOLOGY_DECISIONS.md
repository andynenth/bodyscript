# Technology Stack - Key Decisions

## Quick Decision Guide

### 🎯 For MVP/Prototype (Start Here)
```bash
# Simplest setup to get started
docker-compose up  # Everything in one command

Stack:
- Docker Compose (all-in-one)
- FastAPI + SQLite
- Local file storage
- 1 Celery worker
- Basic React UI

Time to deploy: 1 day
Cost: $0 (local) or $20/month (cloud VM)
```

### 🚀 For Production (Recommended)
```yaml
# Scalable but manageable
Backend: FastAPI + PostgreSQL + Redis
Workers: Celery (2-10 instances)
Storage: MinIO (self-hosted S3)
Deploy: Kubernetes (managed - EKS/GKE/DOKS)
GPU: Optional T4 spot instances
CDN: CloudFlare (free tier)

Time to deploy: 1-2 weeks
Cost: $300-800/month
Handles: 100-500 videos/day
```

### 💡 Critical Technology Choices

| Question | Simple Answer | Why |
|----------|--------------|-----|
| **Docker or no Docker?** | **Docker** | Consistency across environments |
| **Which cloud provider?** | **DigitalOcean** to start, **AWS** to scale | DO is simpler, AWS has more services |
| **Kubernetes or Docker Compose?** | **Compose for <50 users/day, K8s for more** | K8s is overkill for small scale |
| **GPU or CPU only?** | **Start CPU, add GPU later** | GPU costs 3x more but processes 5x faster |
| **Which database?** | **PostgreSQL** | Reliable, well-supported, free |
| **Which queue system?** | **Celery + Redis** | Python native, simple setup |
| **Storage: S3 or self-hosted?** | **MinIO locally, S3 in production** | Control costs while maintaining compatibility |
| **Serverless or servers?** | **Servers** | Video processing too long for Lambda |
| **Monitoring solution?** | **Prometheus + Grafana** | Free, powerful, standard |
| **CI/CD platform?** | **GitHub Actions** | Already using GitHub, generous free tier |

### 🏗️ Architecture Pattern

**Recommended: Queue-Based Processing**
```
Upload → Queue → Worker → Storage → Download
        ↓
    Database (track jobs)
```

**Why this pattern?**
- Handles long-running tasks (videos take minutes)
- Scales horizontally (add more workers)
- Resilient (retry failed jobs)
- User-friendly (show progress)

### 💰 Cost Comparison

| Approach | Monthly Cost | Pros | Cons |
|----------|-------------|------|------|
| **Local Docker** | $0 | Free, full control | No internet access |
| **Single VPS** | $20-80 | Simple, affordable | Limited scale |
| **Managed K8s** | $300-800 | Scalable, reliable | Complex, expensive |
| **Serverless** | $100-2000 | No ops, auto-scale | Expensive for video |
| **Google Colab** | $0-50 | Free GPU, easy | Not for production |

### 🔧 Development Tools

**Essential**
- Docker Desktop
- VS Code
- Postman
- Git

**Recommended**
- K9s (Kubernetes UI)
- MinIO Console
- Redis Commander
- Grafana

**Nice to Have**
- Lens (K8s IDE)
- Datadog (monitoring)
- Sentry (error tracking)

### 📊 Scaling Triggers

When to upgrade your infrastructure:

| Current State | Trigger | Next Step |
|--------------|---------|-----------|
| Local Docker | 10+ users/day | Deploy to cloud VM |
| Single VM | 50+ users/day | Add worker VMs |
| Multiple VMs | 100+ users/day | Move to Kubernetes |
| Basic K8s | 500+ users/day | Add GPU nodes |
| K8s + GPU | 1000+ users/day | Multi-region deployment |

### 🚨 Common Pitfalls to Avoid

1. **Don't start with Kubernetes** - It's overkill for MVP
2. **Don't use Lambda for video processing** - 15-min timeout kills you
3. **Don't store frames permanently** - Delete after processing
4. **Don't process on web server** - Always use background workers
5. **Don't forget cleanup jobs** - Storage fills up fast
6. **Don't skip monitoring** - You'll regret it in production
7. **Don't use latest Python** - MediaPipe needs 3.8-3.11

### 🎬 Quick Start Commands

```bash
# Development (immediate start)
git clone <repo>
cd bodyscript
docker-compose up

# Staging (cloud deployment)
docker-compose -f docker-compose.prod.yml up -d

# Production (Kubernetes)
kubectl apply -f k8s/
kubectl port-forward svc/bodyscript 8000:8000

# GPU Processing (if available)
docker run --gpus all bodyscript-gpu
```

### 📈 Performance Expectations

| Mode | CPU Speed | GPU Speed | Quality |
|------|-----------|-----------|---------|
| Ultra Fast | 10 FPS | 50 FPS | 85% |
| Fast | 5 FPS | 25 FPS | 90% |
| Smart | 3 FPS | 15 FPS | 95% |
| Quality | 0.5 FPS | 3 FPS | 98% |

### ✅ Go/No-Go Checklist

**Ready for MVP?**
- [ ] Docker installed
- [ ] 8GB RAM available
- [ ] Python 3.9 environment
- [ ] 50GB disk space

**Ready for Production?**
- [ ] Cloud account (AWS/GCP/DO)
- [ ] Domain name
- [ ] SSL certificate
- [ ] Monitoring setup
- [ ] Backup strategy
- [ ] Error tracking
- [ ] CI/CD pipeline

## Summary

**Start simple**: Docker Compose + FastAPI + PostgreSQL + Celery

**Scale when needed**: Add Kubernetes, GPU, CDN as you grow

**Focus on**: Getting MVP working first, optimize later

**Remember**: You can always migrate - don't over-engineer Day 1