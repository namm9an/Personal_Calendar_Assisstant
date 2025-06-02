# Calendar Assistant Deployment Guide

## Prerequisites

- Kubernetes cluster (v1.19+)
- Helm v3
- kubectl configured
- Docker registry access
- MongoDB Atlas account
- Redis Cloud account
- Google Cloud Platform account (for OAuth)

## Environment Setup

1. Create a `.env` file with the following variables:
```bash
# MongoDB
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<db>
MONGODB_DB=calendar_assistant

# Redis
REDIS_URL=redis://<username>:<password>@<host>:<port>

# Google OAuth
GOOGLE_CLIENT_ID=<client_id>
GOOGLE_CLIENT_SECRET=<client_secret>
GOOGLE_REDIRECT_URI=https://<your-domain>/auth/callback

# JWT
JWT_SECRET=<your-secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM API
OPENAI_API_KEY=<your-api-key>

# Monitoring
PROMETHEUS_MULTIPROC_DIR=/tmp
```

2. Create Kubernetes secrets:
```bash
kubectl create secret generic calendar-secrets \
  --from-env-file=.env
```

## Deployment Steps

1. Build and push Docker image:
```bash
docker build -t your-registry/calendar-assistant:latest .
docker push your-registry/calendar-assistant:latest
```

2. Install dependencies:
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

3. Deploy the application:
```bash
helm install calendar-assistant ./helm/calendar-assistant \
  --set image.repository=your-registry/calendar-assistant \
  --set image.tag=latest \
  --set ingress.host=your-domain.com \
  --set mongodb.auth.enabled=true \
  --set redis.auth.enabled=true
```

4. Verify deployment:
```bash
kubectl get pods
kubectl get services
kubectl get ingress
```

## Monitoring Setup

1. Access Grafana:
```bash
kubectl port-forward svc/calendar-assistant-grafana 3000:80
```
Visit http://localhost:3000 (default credentials: admin/admin)

2. Import dashboards:
- Navigate to Dashboards > Import
- Upload `monitoring/grafana/dashboards/calendar-assistant.json`

3. Configure alerts:
- Navigate to Alerting > Alert Rules
- Import `monitoring/prometheus/rules/alerts.yml`

## Load Testing

1. Install Locust:
```bash
pip install locust
```

2. Run load test:
```bash
cd tests/load
python locustfile.py
```

3. View results at http://localhost:8089

## Scaling

1. Horizontal Pod Autoscaling:
```bash
kubectl get hpa
```

2. Manual scaling:
```bash
kubectl scale deployment calendar-assistant --replicas=5
```

## Backup and Restore

1. MongoDB backup:
```bash
mongodump --uri="<MONGODB_URI>" --out=/backup
```

2. MongoDB restore:
```bash
mongorestore --uri="<MONGODB_URI>" /backup
```

3. Redis backup:
```bash
redis-cli -u <REDIS_URL> SAVE
```

## Troubleshooting

1. Check pod logs:
```bash
kubectl logs -f deployment/calendar-assistant
```

2. Check MongoDB connection:
```bash
kubectl exec -it deployment/calendar-assistant -- mongosh <MONGODB_URI>
```

3. Check Redis connection:
```bash
kubectl exec -it deployment/calendar-assistant -- redis-cli -u <REDIS_URL>
```

4. Check Prometheus metrics:
```bash
kubectl port-forward svc/calendar-assistant-prometheus-server 9090:9090
```
Visit http://localhost:9090

## Security Considerations

1. Enable TLS:
```bash
kubectl apply -f k8s/tls/cert-manager.yaml
```

2. Configure network policies:
```bash
kubectl apply -f k8s/network-policies/
```

3. Enable RBAC:
```bash
kubectl apply -f k8s/rbac/
```

## Maintenance

1. Update application:
```bash
helm upgrade calendar-assistant ./helm/calendar-assistant \
  --set image.tag=new-version
```

2. Database maintenance:
```bash
kubectl exec -it deployment/calendar-assistant -- python scripts/maintenance.py
```

3. Monitor resource usage:
```bash
kubectl top pods
kubectl top nodes
```

## Disaster Recovery

1. Backup verification:
```bash
python scripts/verify_backup.py
```

2. Restore procedure:
```bash
python scripts/restore.py --backup-dir=/backup
```

3. Failover testing:
```bash
python scripts/test_failover.py
```

## Support

For issues and support:
1. Check logs and metrics in Grafana
2. Review Prometheus alerts
3. Contact system administrator
4. Open GitHub issue

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Redis Cloud Documentation](https://docs.redis.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/) 