# Calendar Assistant Security Guide

## Security Architecture

### Network Security

1. Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: calendar-assistant-network-policy
spec:
  podSelector:
    matchLabels:
      app: calendar-assistant
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: mongodb
    ports:
    - protocol: TCP
      port: 27017
  - to:
    - namespaceSelector:
        matchLabels:
          name: redis
    ports:
    - protocol: TCP
      port: 6379
```

2. TLS Configuration
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: calendar-assistant-cert
spec:
  secretName: calendar-assistant-tls
  issuerRef:
    name: letsencrypt-prod
  dnsNames:
  - your-domain.com
  - www.your-domain.com
```

### Authentication & Authorization

1. JWT Configuration
```python
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

2. OAuth2 Configuration
```python
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
```

3. RBAC Configuration
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: calendar-assistant-role
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: calendar-assistant-role-binding
subjects:
- kind: ServiceAccount
  name: calendar-assistant
  namespace: default
roleRef:
  kind: Role
  name: calendar-assistant-role
  apiGroup: rbac.authorization.k8s.io
```

## Security Measures

### 1. Data Protection

1. Encryption at Rest
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: calendar-assistant-encryption-key
type: Opaque
data:
  key: <base64-encoded-key>
```

2. Encryption in Transit
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: calendar-assistant-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: calendar-assistant-tls
```

### 2. Access Control

1. API Rate Limiting
```python
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/events")
@limiter.limit("100/minute")
async def get_events():
    pass
```

2. IP Whitelisting
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: calendar-assistant-ip-whitelist
spec:
  podSelector:
    matchLabels:
      app: calendar-assistant
  ingress:
  - from:
    - ipBlock:
        cidr: 10.0.0.0/24
```

### 3. Monitoring & Logging

1. Security Logging
```python
import logging
from logging.handlers import RotatingFileHandler

security_logger = logging.getLogger("security")
handler = RotatingFileHandler(
    "security.log",
    maxBytes=10000000,
    backupCount=5
)
security_logger.addHandler(handler)

def log_security_event(event_type, details):
    security_logger.info(f"{event_type}: {details}")
```

2. Audit Logging
```python
def audit_log(user_id, action, resource, status):
    log_security_event(
        "audit",
        {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## Security Best Practices

### 1. Code Security

1. Input Validation
```python
from pydantic import BaseModel, EmailStr, constr

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=100)
    name: constr(min_length=1, max_length=100)
```

2. SQL Injection Prevention
```python
from motor.motor_asyncio import AsyncIOMotorClient

async def get_user(email: str):
    return await db.users.find_one({"email": email})
```

3. XSS Prevention
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 2. Infrastructure Security

1. Container Security
```dockerfile
FROM python:3.9-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. Resource Limits
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: calendar-assistant
spec:
  containers:
  - name: calendar-assistant
    resources:
      requests:
        memory: "256Mi"
        cpu: "200m"
      limits:
        memory: "512Mi"
        cpu: "500m"
```

### 3. Data Security

1. Sensitive Data Handling
```python
from cryptography.fernet import Fernet

def encrypt_sensitive_data(data: str) -> str:
    key = os.getenv("ENCRYPTION_KEY")
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    key = os.getenv("ENCRYPTION_KEY")
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()
```

2. Data Retention
```python
async def cleanup_old_data():
    # Delete events older than 1 year
    await db.events.delete_many({
        "end_time": {"$lt": datetime.utcnow() - timedelta(days=365)}
    })
    
    # Delete logs older than 6 months
    await db.logs.delete_many({
        "timestamp": {"$lt": datetime.utcnow() - timedelta(days=180)}
    })
```

## Security Incident Response

### 1. Incident Classification

1. Critical Incidents
- Unauthorized access to production systems
- Data breach
- Service disruption
- Malware infection

2. High Priority Incidents
- Failed authentication attempts
- Suspicious API activity
- Performance degradation
- Configuration changes

3. Medium Priority Incidents
- Security scan findings
- Compliance violations
- Access control issues
- Logging failures

### 2. Response Procedures

1. Detection
```python
async def detect_security_incident():
    # Monitor failed login attempts
    failed_logins = await db.auth_logs.find({
        "status": "failed",
        "timestamp": {"$gt": datetime.utcnow() - timedelta(minutes=5)}
    }).count()
    
    if failed_logins > 10:
        await notify_security_team("Multiple failed login attempts detected")
```

2. Containment
```python
async def contain_security_incident(ip_address: str):
    # Block suspicious IP
    await db.blocked_ips.insert_one({
        "ip": ip_address,
        "reason": "Suspicious activity",
        "timestamp": datetime.utcnow()
    })
    
    # Update firewall rules
    await update_firewall_rules()
```

3. Eradication
```python
async def eradicate_security_incident():
    # Reset affected user passwords
    await db.users.update_many(
        {"last_login_ip": suspicious_ip},
        {"$set": {"password": generate_secure_password()}}
    )
    
    # Revoke affected sessions
    await db.sessions.delete_many({"user_ip": suspicious_ip})
```

4. Recovery
```python
async def recover_from_incident():
    # Verify system integrity
    await verify_system_integrity()
    
    # Restore from backup if necessary
    if system_compromised:
        await restore_from_backup()
    
    # Resume normal operations
    await resume_operations()
```

## Security Monitoring

### 1. Real-time Monitoring

1. Security Metrics
```python
from prometheus_client import Counter, Histogram

security_events = Counter(
    'security_events_total',
    'Total number of security events',
    ['event_type', 'severity']
)

auth_attempts = Histogram(
    'auth_attempts_duration_seconds',
    'Duration of authentication attempts',
    ['status']
)
```

2. Alert Rules
```yaml
groups:
- name: security
  rules:
  - alert: HighFailedLoginAttempts
    expr: rate(security_events_total{event_type="failed_login"}[5m]) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High number of failed login attempts
```

### 2. Security Scanning

1. Dependency Scanning
```bash
# Scan Python dependencies
safety check

# Scan Docker images
trivy image your-registry/calendar-assistant:latest
```

2. Code Scanning
```bash
# Run bandit for security checks
bandit -r .

# Run semgrep for security checks
semgrep --config=p/security-audit .
```

## Compliance

### 1. Data Protection

1. GDPR Compliance
```python
async def handle_data_deletion_request(user_id: str):
    # Delete user data
    await db.users.delete_one({"_id": user_id})
    await db.events.delete_many({"user_id": user_id})
    await db.sessions.delete_many({"user_id": user_id})
    
    # Log deletion
    await log_data_deletion(user_id)
```

2. Data Export
```python
async def export_user_data(user_id: str):
    # Collect user data
    user_data = {
        "profile": await db.users.find_one({"_id": user_id}),
        "events": await db.events.find({"user_id": user_id}).to_list(None),
        "sessions": await db.sessions.find({"user_id": user_id}).to_list(None)
    }
    
    # Export data
    return json.dumps(user_data, default=str)
```

### 2. Security Standards

1. OWASP Top 10
- Implement input validation
- Use parameterized queries
- Enable security headers
- Implement proper authentication
- Use secure session management

2. Security Headers
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## Security Training

### 1. Developer Training

1. Secure Coding Guidelines
- Input validation
- Output encoding
- Error handling
- Authentication
- Authorization
- Session management
- Cryptography
- File handling

2. Code Review Checklist
- Security vulnerabilities
- Authentication issues
- Authorization issues
- Data exposure
- Input validation
- Error handling
- Logging
- Configuration

### 2. Operations Training

1. Security Procedures
- Incident response
- Access management
- Configuration management
- Monitoring
- Logging
- Backup and restore
- Disaster recovery

2. Security Tools
- Vulnerability scanners
- Security monitoring
- Log analysis
- Network monitoring
- Access control
- Encryption tools

## Security Documentation

### 1. Security Policies

1. Access Control Policy
- User authentication
- Role-based access control
- Password policies
- Session management
- API access control

2. Data Protection Policy
- Data classification
- Data handling
- Data retention
- Data disposal
- Data backup

### 2. Security Procedures

1. Incident Response Procedure
- Detection
- Analysis
- Containment
- Eradication
- Recovery
- Post-incident review

2. Security Maintenance Procedure
- Security updates
- Vulnerability management
- Configuration management
- Access review
- Security testing 