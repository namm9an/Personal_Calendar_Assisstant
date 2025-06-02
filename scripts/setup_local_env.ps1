# Setup Local Development Environment

Write-Host "Setting up local development environment..." -ForegroundColor Green

# Check if Chocolatey is installed
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

# Install required tools
Write-Host "Installing required tools..." -ForegroundColor Yellow
choco install minikube kubernetes-cli docker-desktop mongodb redis -y

# Start Docker Desktop
Write-Host "Starting Docker Desktop..." -ForegroundColor Yellow
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Wait for Docker to start
Write-Host "Waiting for Docker to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Start Minikube
Write-Host "Starting Minikube..." -ForegroundColor Yellow
minikube start --driver=docker --cpus=4 --memory=8192

# Enable required addons
Write-Host "Enabling Minikube addons..." -ForegroundColor Yellow
minikube addons enable ingress
minikube addons enable metrics-server

# Create namespaces
Write-Host "Creating Kubernetes namespaces..." -ForegroundColor Yellow
kubectl create namespace production
kubectl create namespace monitoring
kubectl create namespace mongodb
kubectl create namespace redis

# Label namespaces
Write-Host "Labeling namespaces..." -ForegroundColor Yellow
kubectl label namespace monitoring name=monitoring
kubectl label namespace mongodb name=mongodb
kubectl label namespace redis name=redis

# Create .env file
Write-Host "Creating .env file..." -ForegroundColor Yellow
$envContent = @"
# MongoDB Configuration
MONGODB_URI=mongodb://mongodb:27017/calendar_assistant

# Redis Configuration
REDIS_URI=redis://redis:6379/0

# Application Configuration
TEST_BASE_URL=http://localhost:8000
TEST_NAMESPACE=production

# Monitoring Configuration
GRAFANA_URL=http://localhost:3000
PROMETHEUS_URL=http://localhost:9090

# Security Configuration
JWT_SECRET=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# LLM API Configuration
LLM_API_KEY=your_llm_api_key
LLM_API_URL=https://api.openai.com/v1
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8

Write-Host "Local environment setup completed!" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "1. Update the .env file with your actual credentials"
Write-Host "2. Run 'kubectl get pods -A' to verify all components are running"
Write-Host "3. Run './scripts/deploy_local.ps1' to deploy the application" 