# Deploy Calendar Assistant to Local Kubernetes Cluster

Write-Host "Deploying Calendar Assistant..." -ForegroundColor Green

# Build Docker image
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker build -t calendar-assistant:latest .

# Load image into Minikube
Write-Host "Loading image into Minikube..." -ForegroundColor Yellow
minikube image load calendar-assistant:latest

# Create Kubernetes secrets from .env file
Write-Host "Creating Kubernetes secrets..." -ForegroundColor Yellow
$envContent = Get-Content .env -Raw
$envContent | kubectl create secret generic calendar-assistant-secrets --from-env-file=/dev/stdin -n production

# Deploy MongoDB
Write-Host "Deploying MongoDB..." -ForegroundColor Yellow
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install mongodb bitnami/mongodb -n mongodb -f k8s/values/mongodb-values.yaml

# Deploy Redis
Write-Host "Deploying Redis..." -ForegroundColor Yellow
helm install redis bitnami/redis -n redis -f k8s/values/redis-values.yaml

# Deploy Prometheus
Write-Host "Deploying Prometheus..." -ForegroundColor Yellow
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/prometheus -n monitoring -f k8s/values/prometheus-values.yaml

# Deploy Grafana
Write-Host "Deploying Grafana..." -ForegroundColor Yellow
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install grafana grafana/grafana -n monitoring -f k8s/values/grafana-values.yaml

# Deploy Calendar Assistant
Write-Host "Deploying Calendar Assistant..." -ForegroundColor Yellow
kubectl apply -f k8s/base/network-policy.yaml
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/base/deployment.yaml
kubectl apply -f k8s/base/service.yaml

# Wait for deployments to be ready
Write-Host "Waiting for deployments to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=available --timeout=300s deployment/calendar-assistant -n production
kubectl wait --for=condition=available --timeout=300s deployment/mongodb -n mongodb
kubectl wait --for=condition=available --timeout=300s deployment/redis -n redis

# Get service URLs
$minikubeIP = minikube ip
Write-Host "`nService URLs:" -ForegroundColor Green
Write-Host "Calendar Assistant: http://$minikubeIP:8000" -ForegroundColor Yellow
Write-Host "Grafana: http://$minikubeIP:3000" -ForegroundColor Yellow
Write-Host "Prometheus: http://$minikubeIP:9090" -ForegroundColor Yellow

Write-Host "`nDeployment completed!" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "1. Run './scripts/run_phase4_validation.ps1' to validate the deployment"
Write-Host "2. Check the logs with 'kubectl logs -f deployment/calendar-assistant -n production'"
Write-Host "3. Monitor the application with 'kubectl get pods -A'" 