# Phase 4 Validation Test Runner (PowerShell Version)

Write-Host "Starting Phase 4 Validation Tests" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green

# Set environment variables
$env:TEST_BASE_URL = "https://calendar-assistant.example.com"
$env:TEST_NAMESPACE = "production"
$env:GRAFANA_URL = "https://grafana.example.com"
$env:PROMETHEUS_URL = "https://prometheus.example.com"

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install -r requirements-test.txt

# Run validation tests
Write-Host "Running validation tests..." -ForegroundColor Yellow
python tests/phase4_validation.py

# Check test results
if ($LASTEXITCODE -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
    Write-Host "Phase 4 validation completed successfully." -ForegroundColor Green
} else {
    Write-Host "Some tests failed!" -ForegroundColor Red
    Write-Host "Please check the test output for details." -ForegroundColor Red
    exit 1
}

# Generate test report
Write-Host "Generating test report..." -ForegroundColor Yellow
python scripts/generate_test_report.py

Write-Host "Phase 4 validation completed!" -ForegroundColor Green 