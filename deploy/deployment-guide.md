# BodyScript Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying BodyScript to staging and production environments. The deployment process uses a combination of automated CI/CD pipelines and manual deployment scripts for maximum flexibility and safety.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│   CI Pipeline   │───▶│  Staging Env    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                │                        ▼
                                │              ┌─────────────────┐
                                │              │   Manual QA     │
                                │              └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Production Deploy│    │ Production Env  │
                       └─────────────────┘    └─────────────────┘
```

## Deployment Environments

### Staging Environment
- **URL:** https://bodyscript-staging.example.com
- **API:** https://api-staging.bodyscript.example.com
- **Purpose:** Integration testing, QA validation, stakeholder preview
- **Auto-deploy:** Yes (on push to `develop` branch)
- **Data:** Synthetic test data, safe for experimentation

### Production Environment
- **URL:** https://bodyscript.com
- **API:** https://api.bodyscript.com
- **Purpose:** Live user-facing application
- **Auto-deploy:** Manual approval required
- **Data:** Real user data, requires careful handling

## Prerequisites

### Required Tools
```bash
# Install required CLI tools
npm install -g @aws-cli/aws-cli
npm install -g github-cli
pip install awscli boto3
```

### Environment Setup
```bash
# Configure AWS credentials
aws configure --profile bodyscript-staging
aws configure --profile bodyscript-production

# Set up environment variables
cp .env.example .env.staging
cp .env.example .env.production

# Edit configuration files
vim .env.staging
vim .env.production
```

### Required Secrets
Set up the following secrets in GitHub repository settings:

#### Staging Secrets
- `STAGING_API_URL`
- `STAGING_S3_BUCKET`
- `STAGING_CLOUDFRONT_ID`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

#### Production Secrets
- `PRODUCTION_API_URL`
- `PRODUCTION_S3_BUCKET`
- `PRODUCTION_CLOUDFRONT_ID`
- `ECR_REGISTRY`
- `SENTRY_DSN`
- `SLACK_WEBHOOK`

## Deployment Methods

### 1. Automated CI/CD Pipeline (Recommended)

#### Staging Deployment
```bash
# Automatic deployment on push to develop
git checkout develop
git add .
git commit -m "feature: add new functionality"
git push origin develop

# Monitor deployment progress
gh workflow view "Deploy to Staging" --web
```

#### Production Deployment
```bash
# Create production release
git checkout main
git merge develop
git tag v1.2.3
git push origin main --tags

# Monitor deployment (requires manual approval)
gh workflow view "Deploy to Production" --web
```

### 2. Manual Deployment Scripts

#### Staging Deployment
```bash
# Deploy to staging manually
./deploy/staging.sh

# Or with specific environment settings
NODE_ENV=staging ./deploy/staging.sh
```

#### Production Deployment
```bash
# Deploy to production (requires confirmation)
./deploy/production.sh

# Force deployment without confirmation (dangerous)
./deploy/production.sh --force
```

## Deployment Process Flow

### Staging Deployment Flow

1. **Pre-deployment Checks**
   - Verify branch is `develop`
   - Check for uncommitted changes
   - Validate environment configuration
   - Check system resources

2. **Dependency Installation**
   - Install Node.js dependencies
   - Install Python dependencies
   - Security audit of packages

3. **Test Execution**
   - Run unit tests
   - Run linting checks
   - Basic integration tests

4. **Build Process**
   - Build frontend with staging configuration
   - Build backend Python package
   - Generate build manifest

5. **Deployment**
   - Deploy frontend to S3
   - Deploy backend to ECS
   - Update CloudFront distribution
   - Restart services

6. **Validation**
   - Health checks on all endpoints
   - Smoke tests
   - Performance validation

### Production Deployment Flow

1. **Enhanced Pre-deployment Checks**
   - Verify branch is `main`
   - Check staging environment health
   - Validate version tags
   - Comprehensive system checks

2. **Comprehensive Testing**
   - Full test suite execution
   - Security audits
   - Performance tests
   - End-to-end tests

3. **Backup Creation**
   - Create deployment backup
   - Database snapshot
   - Configuration backup

4. **Blue-Green Deployment**
   - Deploy to inactive environment
   - Comprehensive health checks
   - Traffic switch
   - Old environment cleanup

5. **Post-deployment Monitoring**
   - Real-time monitoring setup
   - Performance metrics collection
   - Error rate monitoring
   - User experience validation

## Configuration Management

### Environment Files

#### Staging Configuration (.env.staging)
```bash
NODE_ENV=staging
VITE_API_URL=https://api-staging.bodyscript.example.com
VITE_ENVIRONMENT=staging
VITE_DEBUG=true
VITE_SENTRY_DSN=https://your-staging-sentry-dsn

# Database
DATABASE_URL=postgresql://user:pass@staging-db.example.com:5432/bodyscript_staging

# Storage
AWS_S3_BUCKET=bodyscript-staging-storage
AWS_REGION=us-east-1

# Processing
MEDIAPIPE_MODEL_PATH=/models/pose_landmarker_heavy.task
PROCESSING_CONCURRENCY=2

# Monitoring
LOG_LEVEL=debug
METRICS_ENABLED=true
```

#### Production Configuration (.env.production)
```bash
NODE_ENV=production
VITE_API_URL=https://api.bodyscript.com
VITE_ENVIRONMENT=production
VITE_DEBUG=false
VITE_SENTRY_DSN=https://your-production-sentry-dsn

# Database
DATABASE_URL=postgresql://user:pass@prod-db.example.com:5432/bodyscript

# Storage
AWS_S3_BUCKET=bodyscript-production-storage
AWS_REGION=us-east-1

# Processing
MEDIAPIPE_MODEL_PATH=/models/pose_landmarker_heavy.task
PROCESSING_CONCURRENCY=4

# Monitoring
LOG_LEVEL=info
METRICS_ENABLED=true
PERFORMANCE_MONITORING=true
```

## Build Process

### Frontend Build
```bash
# Development build
npm run build:dev

# Staging build
npm run build:staging

# Production build (optimized)
npm run build:prod
```

### Backend Build
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Build Python package
python setup.py build

# Create distribution
python setup.py sdist bdist_wheel
```

## Health Checks

### Frontend Health Check
```bash
curl -f https://bodyscript.com/
```

### API Health Check
```bash
curl -f https://api.bodyscript.com/health
```

### Database Health Check
```bash
curl -f https://api.bodyscript.com/health/database
```

### Processing Health Check
```bash
curl -f https://api.bodyscript.com/health/pose
```

## Rollback Procedures

### Quick Rollback
```bash
# Rollback to previous version
./deploy/rollback.sh production

# Rollback to specific version
./deploy/rollback.sh production --version 20240924_143022

# List available backups
./deploy/rollback.sh --list production
```

### Emergency Rollback
```bash
# Force rollback without confirmation
./deploy/rollback.sh production --force

# Emergency database rollback
./deploy/rollback.sh production --version latest --database-only
```

## Monitoring and Alerting

### Deployment Monitoring
```bash
# Monitor deployment logs
aws logs tail /aws/ecs/bodyscript-production --follow

# Check deployment metrics
aws cloudwatch get-metric-statistics \
    --namespace "BodyScript/Deployment" \
    --metric-name "DeploymentDuration" \
    --start-time 2024-09-24T10:00:00Z \
    --end-time 2024-09-24T11:00:00Z \
    --period 300 \
    --statistics Average
```

### Real-time Alerts
- **Slack:** `#deployments` channel
- **Email:** deployment-alerts@bodyscript.com
- **PagerDuty:** Critical failures only

## Troubleshooting

### Common Issues

#### Build Failures
```bash
# Clear node modules and rebuild
rm -rf node_modules package-lock.json
npm install

# Clear Python cache
find . -type d -name __pycache__ -delete
find . -name "*.pyc" -delete
```

#### Deployment Timeouts
```bash
# Check ECS service status
aws ecs describe-services \
    --cluster bodyscript-production \
    --services bodyscript-api-production

# Increase task timeout
aws ecs update-service \
    --cluster bodyscript-production \
    --service bodyscript-api-production \
    --deployment-configuration maximumPercent=200,minimumHealthyPercent=50
```

#### Database Connection Issues
```bash
# Check RDS instance status
aws rds describe-db-instances \
    --db-instance-identifier bodyscript-production

# Test database connectivity
psql $DATABASE_URL -c "SELECT version();"
```

### Debug Commands

#### Check Service Logs
```bash
# ECS service logs
aws logs tail /aws/ecs/bodyscript-production

# CloudFront logs
aws logs tail /aws/cloudfront/bodyscript-distribution

# Application logs
kubectl logs -f deployment/bodyscript-api
```

#### Performance Debugging
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s https://bodyscript.com/

# Database performance
psql $DATABASE_URL -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

## Security Considerations

### Secrets Management
- Use AWS Secrets Manager for production secrets
- Rotate API keys quarterly
- Use IAM roles instead of access keys where possible
- Encrypt sensitive configuration values

### Access Control
- Limit deployment access to authorized personnel
- Use MFA for production deployments
- Audit deployment activities
- Implement least privilege access

### Network Security
- Deploy behind WAF (Web Application Firewall)
- Use VPC with private subnets
- Implement network ACLs
- Regular security scans

## Maintenance Windows

### Scheduled Maintenance
- **Staging:** No restrictions
- **Production:** Sundays 2:00-4:00 AM UTC (during low traffic)

### Emergency Maintenance
- Can be performed any time with proper escalation
- Must include incident commander
- Requires stakeholder notification

## Performance Optimization

### Frontend Optimization
- Enable Gzip compression
- Use CDN for static assets
- Implement lazy loading
- Optimize bundle sizes

### Backend Optimization
- Database query optimization
- API response caching
- Connection pooling
- Resource limits tuning

### Infrastructure Optimization
- Auto-scaling configuration
- Load balancer optimization
- Database performance tuning
- Monitoring and alerting fine-tuning

## Disaster Recovery

See [Disaster Recovery Plan](./disaster-recovery.md) for detailed procedures.

### Key Recovery Metrics
- **RTO:** 15 minutes for critical services
- **RPO:** 5 minutes for database
- **Data Backup:** Every 6 hours with cross-region replication
- **Service Backup:** Blue-green deployment with instant fallback

---

## Contact Information

- **DevOps Team:** devops@bodyscript.com
- **On-call Support:** +1-555-DEPLOY
- **Emergency Escalation:** emergency@bodyscript.com

Last Updated: 2024-09-24
Next Review: 2024-12-24