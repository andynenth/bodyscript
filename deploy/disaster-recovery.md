# BodyScript Disaster Recovery Plan

## Overview

This document outlines the disaster recovery procedures for BodyScript, covering various failure scenarios and recovery steps for both staging and production environments.

## Recovery Time Objectives (RTO) & Recovery Point Objectives (RPO)

| Service Component | RTO | RPO | Priority |
|------------------|-----|-----|----------|
| Frontend (Static) | 5 minutes | 1 hour | Critical |
| API Service | 15 minutes | 5 minutes | Critical |
| Database | 30 minutes | 15 minutes | Critical |
| File Storage | 1 hour | 1 hour | High |
| Processing Queue | 2 hours | 30 minutes | Medium |
| Analytics | 24 hours | 24 hours | Low |

## Disaster Scenarios & Response

### 1. Complete Site Outage

**Symptoms:**
- Frontend and API completely unreachable
- Health checks failing across all endpoints
- Multiple alerts triggered

**Immediate Response (0-5 minutes):**
```bash
# 1. Check system status
./deploy/rollback.sh --list production

# 2. Verify AWS service status
aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name RunningTaskCount

# 3. Emergency rollback if recent deployment
./deploy/rollback.sh production --force

# 4. Check CloudFront and ALB status
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:us-east-1:ACCOUNT:targetgroup/bodyscript-api/ID
```

**Recovery Steps (5-30 minutes):**
1. Activate incident response team
2. Enable maintenance mode page
3. Restore from latest known-good backup
4. Scale ECS services to multiple AZs
5. Validate core functionality

### 2. Database Failure

**Symptoms:**
- API returning database connection errors
- `/api/health/database` endpoint failing
- RDS monitoring shows connection issues

**Immediate Response:**
```bash
# 1. Check RDS instance status
aws rds describe-db-instances --db-instance-identifier bodyscript-production

# 2. Check backup availability
aws rds describe-db-snapshots --db-instance-identifier bodyscript-production

# 3. If corruption, restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier bodyscript-production-restored \
    --db-snapshot-identifier bodyscript-production-snapshot-20240924
```

**Recovery Steps:**
1. Point application to restored database
2. Update DNS/connection strings
3. Verify data integrity
4. Resume normal operations
5. Investigate root cause

### 3. Regional AWS Failure

**Symptoms:**
- Multiple AWS services unavailable in us-east-1
- Cannot connect to any AWS resources
- Cross-region backups needed

**Recovery Steps:**
1. **Activate DR Region (us-west-2):**
   ```bash
   # Deploy to backup region
   aws configure set region us-west-2

   # Restore from cross-region backup
   aws s3 sync s3://bodyscript-backup-us-west-2/latest/ s3://bodyscript-production-us-west-2/

   # Update Route 53 to point to DR region
   aws route53 change-resource-record-sets --hosted-zone-id Z123456 --change-batch file://dr-dns-change.json
   ```

2. **Scale up DR infrastructure:**
   - Increase ECS task count
   - Restore database from cross-region snapshot
   - Activate CloudFront distribution for DR

3. **Communicate with users:**
   - Update status page
   - Send notifications about temporary service location

### 4. Data Corruption/Loss

**Symptoms:**
- Users reporting missing or incorrect data
- Database integrity checks failing
- Unexpected data patterns in analytics

**Recovery Steps:**
1. **Immediate isolation:**
   ```bash
   # Stop write operations
   aws ecs update-service --cluster bodyscript-production --service bodyscript-api --desired-count 0

   # Enable read-only mode
   kubectl set env deployment/bodyscript-api DATABASE_READ_ONLY=true
   ```

2. **Assess corruption scope:**
   ```bash
   # Check database integrity
   sudo -u postgres psql -d bodyscript -c "REINDEX DATABASE bodyscript;"

   # Analyze recent changes
   sudo -u postgres psql -d bodyscript -c "SELECT * FROM audit_log WHERE created_at > NOW() - INTERVAL '24 hours';"
   ```

3. **Restore from point-in-time:**
   ```bash
   # Create point-in-time recovery
   aws rds restore-db-instance-to-point-in-time \
       --source-db-instance-identifier bodyscript-production \
       --target-db-instance-identifier bodyscript-recovery \
       --restore-time 2024-09-24T10:00:00.000Z
   ```

### 5. Security Incident

**Symptoms:**
- Unusual access patterns
- Unauthorized API calls
- Security monitoring alerts

**Immediate Response (0-15 minutes):**
1. **Isolate affected systems:**
   ```bash
   # Block suspicious IPs
   aws ec2 authorize-security-group-ingress --group-id sg-12345678 --protocol tcp --port 443 --source-group sg-87654321

   # Rotate API keys
   aws iam create-access-key --user-name bodyscript-api
   aws iam delete-access-key --user-name bodyscript-api --access-key-id OLDKEY
   ```

2. **Enable audit mode:**
   ```bash
   # Enable comprehensive logging
   aws logs put-retention-policy --log-group-name /aws/ecs/bodyscript-production --retention-in-days 30

   # Enable CloudTrail
   aws cloudtrail start-logging --name bodyscript-security-trail
   ```

3. **Preserve evidence:**
   - Snapshot affected instances
   - Export logs to secure location
   - Document timeline of events

## Emergency Contacts

### Primary On-Call Rotation
| Role | Primary | Secondary | Escalation |
|------|---------|-----------|------------|
| DevOps Lead | John Doe (+1-555-0101) | Jane Smith (+1-555-0102) | CTO (+1-555-0100) |
| Security Lead | Bob Wilson (+1-555-0201) | Alice Brown (+1-555-0202) | CISO (+1-555-0200) |
| Infrastructure | Mike Davis (+1-555-0301) | Sarah Lee (+1-555-0302) | VP Eng (+1-555-0300) |

### External Vendors
- **AWS Support:** Enterprise Support Case
- **CloudFlare Support:** +1-888-993-5273
- **Database Expert:** contractor@example.com
- **Security Consultant:** security@example.com

## Communication Plan

### Internal Communications
1. **Slack Channel:** `#incident-response`
2. **War Room:** Zoom room ID 123-456-789
3. **Status Updates:** Every 15 minutes during active incident

### External Communications
1. **Status Page:** https://status.bodyscript.com
2. **User Notifications:** Email + in-app notifications
3. **Social Media:** @bodyscript Twitter account

### Communication Templates

#### Initial Incident Notification
```
🚨 INCIDENT ALERT 🚨

Service: BodyScript Production
Status: Investigating
Impact: [High/Medium/Low]
Start Time: [Timestamp]
Description: [Brief description]

We are investigating reports of [issue]. Updates will be posted every 15 minutes.

Next Update: [Time]
Incident Commander: [Name]
```

#### Resolution Notification
```
✅ INCIDENT RESOLVED ✅

Service: BodyScript Production
Status: Resolved
Duration: [X hours Y minutes]
Root Cause: [Brief explanation]

All services have been restored to normal operation. A full post-mortem will be published within 48 hours.

We apologize for any inconvenience caused.
```

## Recovery Verification Checklist

After any recovery procedure, verify the following:

### Functional Testing
- [ ] Frontend loads successfully
- [ ] User authentication works
- [ ] Video upload functionality
- [ ] Pose processing pipeline
- [ ] Data export features
- [ ] Gallery view and navigation

### Performance Testing
- [ ] Page load times < 2 seconds
- [ ] API response times < 500ms
- [ ] Database query performance
- [ ] File upload/download speeds
- [ ] Processing queue latency

### Security Testing
- [ ] SSL certificates valid
- [ ] Authentication endpoints secure
- [ ] API rate limiting active
- [ ] Access logs capturing events
- [ ] Monitoring alerts functional

### Data Integrity
- [ ] User accounts accessible
- [ ] Video files retrievable
- [ ] Pose data accuracy
- [ ] Export data completeness
- [ ] Database referential integrity

## Post-Incident Procedures

### Immediate (0-4 hours)
1. **Stabilize services** and confirm full restoration
2. **Document timeline** of events and actions taken
3. **Preserve evidence** for root cause analysis
4. **Notify stakeholders** of resolution

### Short-term (4-24 hours)
1. **Root cause analysis** with technical team
2. **Update monitoring** to catch similar issues
3. **Review response effectiveness**
4. **Create action items** for improvements

### Long-term (1-7 days)
1. **Publish post-mortem** with lessons learned
2. **Implement preventive measures**
3. **Update runbooks** based on experience
4. **Conduct team retrospective**
5. **Test recovery procedures**

## Backup Verification

### Daily Checks
```bash
# Verify backup creation
aws s3 ls s3://bodyscript-backups/daily/ --recursive | tail -1

# Check backup integrity
aws s3api head-object --bucket bodyscript-backups --key daily/backup-$(date +%Y%m%d).tar.gz

# Verify cross-region replication
aws s3 ls s3://bodyscript-backups-us-west-2/daily/ --recursive | tail -1
```

### Weekly Recovery Tests
```bash
# Test database restore (on staging)
./deploy/rollback.sh staging --version $(date -d '7 days ago' +%Y%m%d)

# Verify data integrity
python scripts/verify-backup-integrity.py --environment staging

# Test cross-region failover
./scripts/test-dr-failover.sh --dry-run
```

## Monitoring and Alerting

### Critical Alerts (Immediate Response)
- Service completely down (PagerDuty)
- Database connectivity lost (PagerDuty)
- Security breach detected (Phone + SMS)
- Data corruption detected (Phone + SMS)

### Warning Alerts (Within 30 minutes)
- High error rate (Slack)
- Slow response times (Slack)
- Resource utilization high (Slack)
- Backup failures (Email)

### Information Alerts (Within 2 hours)
- Deployment completed (Slack)
- Scheduled maintenance (Email)
- Performance degradation (Slack)

## Documentation Updates

This disaster recovery plan should be:
- **Reviewed quarterly** by the engineering team
- **Updated immediately** after any incident
- **Tested annually** with full DR simulation
- **Accessible offline** in case of complete outage

Last Updated: 2024-09-24
Next Review: 2024-12-24
Document Owner: DevOps Team