# Calendar Assistant Production Runbook

## System Overview

The Calendar Assistant is a cloud-native application that helps users manage their calendar events using AI. The system consists of:

- FastAPI backend service
- MongoDB database (Atlas)
- Redis cache
- Prometheus monitoring
- Grafana dashboards
- Kubernetes deployment

## Architecture

```
[Client] → [Load Balancer] → [Kubernetes Ingress] → [Calendar Assistant Pods]
                                                      ↓
[Prometheus] ← [Metrics] ← [Calendar Assistant] → [MongoDB Atlas]
                                                      ↓
[Grafana] ← [Alert Manager] ← [Prometheus] → [Redis Cache]
```

## Health Checks

### Application Health

1. Check application status:
```bash
curl https://your-domain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "mongodb": "connected",
    "redis": "connected"
  }
}
```

2. Check metrics endpoint:
```bash
curl https://your-domain.com/metrics
```

### Database Health

1. Check MongoDB connection:
```bash
kubectl exec -it deployment/calendar-assistant -- python scripts/check_mongodb.py
```

2. Check Redis connection:
```bash
kubectl exec -it deployment/calendar-assistant -- python scripts/check_redis.py
```

## Monitoring

### Key Metrics

1. Application Metrics:
- Request rate
- Error rate
- Response time
- Active users
- Calendar operations

2. System Metrics:
- CPU usage
- Memory usage
- Disk usage
- Network I/O

3. Database Metrics:
- Connection pool
- Query performance
- Cache hit rate
- Replication lag

### Alert Thresholds

1. Critical Alerts:
- Error rate > 5%
- Service down > 1 minute
- Database connection lost
- Memory usage > 90%

2. Warning Alerts:
- Response time > 1s
- CPU usage > 80%
- Disk usage > 80%
- Cache hit rate < 70%

## Common Issues

### 1. High Error Rate

Symptoms:
- Increased error rate in Grafana
- Alert triggered
- User complaints

Actions:
1. Check application logs:
```bash
kubectl logs -f deployment/calendar-assistant
```

2. Check MongoDB logs:
```bash
kubectl logs -f deployment/mongodb
```

3. Check Redis logs:
```bash
kubectl logs -f deployment/redis
```

4. Verify dependencies:
```bash
kubectl exec -it deployment/calendar-assistant -- python scripts/check_dependencies.py
```

### 2. High Latency

Symptoms:
- Slow response times
- Timeout errors
- User complaints

Actions:
1. Check resource usage:
```bash
kubectl top pods
kubectl top nodes
```

2. Check database performance:
```bash
kubectl exec -it deployment/calendar-assistant -- python scripts/check_db_performance.py
```

3. Check cache hit rate:
```bash
kubectl exec -it deployment/calendar-assistant -- python scripts/check_cache.py
```

### 3. Database Issues

Symptoms:
- Connection errors
- Slow queries
- Replication lag

Actions:
1. Check MongoDB status:
```bash
kubectl exec -it deployment/calendar-assistant -- mongosh <MONGODB_URI> --eval "db.serverStatus()"
```

2. Check Redis status:
```bash
kubectl exec -it deployment/calendar-assistant -- redis-cli -u <REDIS_URL> info
```

3. Verify backups:
```bash
python scripts/verify_backup.py
```

## Scaling Procedures

### Horizontal Scaling

1. Check current load:
```bash
kubectl get hpa
kubectl describe hpa calendar-assistant
```

2. Manual scaling:
```bash
kubectl scale deployment calendar-assistant --replicas=5
```

3. Verify scaling:
```bash
kubectl get pods
kubectl get endpoints
```

### Vertical Scaling

1. Update resource limits:
```bash
kubectl patch deployment calendar-assistant -p '{"spec":{"template":{"spec":{"containers":[{"name":"calendar-assistant","resources":{"limits":{"cpu":"2","memory":"4Gi"}}}]}}}}'
```

2. Verify changes:
```bash
kubectl describe pod -l app=calendar-assistant
```

## Backup and Restore

### Backup Procedure

1. MongoDB backup:
```bash
python scripts/backup_mongodb.py --output=/backup
```

2. Redis backup:
```bash
python scripts/backup_redis.py --output=/backup
```

3. Verify backup:
```bash
python scripts/verify_backup.py --backup-dir=/backup
```

### Restore Procedure

1. Stop application:
```bash
kubectl scale deployment calendar-assistant --replicas=0
```

2. Restore MongoDB:
```bash
python scripts/restore_mongodb.py --backup-dir=/backup
```

3. Restore Redis:
```bash
python scripts/restore_redis.py --backup-dir=/backup
```

4. Start application:
```bash
kubectl scale deployment calendar-assistant --replicas=3
```

## Security Incidents

### 1. Unauthorized Access

Symptoms:
- Failed login attempts
- Suspicious API calls
- Alert triggered

Actions:
1. Check access logs:
```bash
kubectl logs -f deployment/calendar-assistant | grep "unauthorized"
```

2. Check IP addresses:
```bash
kubectl exec -it deployment/calendar-assistant -- python scripts/check_suspicious_ips.py
```

3. Update firewall rules:
```bash
kubectl apply -f k8s/network-policies/block-suspicious-ips.yaml
```

### 2. Data Breach

Symptoms:
- Unusual data access patterns
- Alert triggered
- User complaints

Actions:
1. Isolate affected systems:
```bash
kubectl scale deployment calendar-assistant --replicas=0
```

2. Preserve evidence:
```bash
python scripts/preserve_evidence.py
```

3. Notify stakeholders:
```bash
python scripts/notify_security_team.py
```

## Maintenance Procedures

### 1. Application Update

1. Backup data:
```bash
python scripts/backup_all.py
```

2. Update application:
```bash
helm upgrade calendar-assistant ./helm/calendar-assistant --set image.tag=new-version
```

3. Verify update:
```bash
kubectl rollout status deployment/calendar-assistant
```

### 2. Database Maintenance

1. Check database health:
```bash
python scripts/check_db_health.py
```

2. Run maintenance:
```bash
python scripts/run_db_maintenance.py
```

3. Verify maintenance:
```bash
python scripts/verify_db_health.py
```

## Disaster Recovery

### 1. Complete System Failure

1. Verify backup:
```bash
python scripts/verify_backup.py
```

2. Restore system:
```bash
python scripts/restore_system.py
```

3. Verify restoration:
```bash
python scripts/verify_system.py
```

### 2. Partial System Failure

1. Identify affected components:
```bash
python scripts/check_system_health.py
```

2. Restore components:
```bash
python scripts/restore_components.py
```

3. Verify components:
```bash
python scripts/verify_components.py
```

## Contact Information

### Emergency Contacts

1. Primary On-Call:
- Name: [Primary On-Call]
- Phone: [Phone Number]
- Email: [Email]

2. Secondary On-Call:
- Name: [Secondary On-Call]
- Phone: [Phone Number]
- Email: [Email]

3. Database Administrator:
- Name: [DBA]
- Phone: [Phone Number]
- Email: [Email]

### Escalation Path

1. Level 1: Primary On-Call
2. Level 2: Secondary On-Call
3. Level 3: Database Administrator
4. Level 4: System Architect
5. Level 5: CTO

## Appendix

### A. Common Commands

```bash
# Check pod status
kubectl get pods

# Check service status
kubectl get services

# Check ingress status
kubectl get ingress

# Check logs
kubectl logs -f deployment/calendar-assistant

# Check metrics
curl https://your-domain.com/metrics

# Check health
curl https://your-domain.com/health
```

### B. Useful Scripts

1. Health Check:
```bash
python scripts/check_health.py
```

2. Performance Check:
```bash
python scripts/check_performance.py
```

3. Security Check:
```bash
python scripts/check_security.py
```

### C. Monitoring URLs

1. Grafana: https://grafana.your-domain.com
2. Prometheus: https://prometheus.your-domain.com
3. Alert Manager: https://alertmanager.your-domain.com 