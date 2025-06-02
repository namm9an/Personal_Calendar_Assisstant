#!/bin/bash

# Phase 4 Validation Test Runner

echo "🚀 Starting Phase 4 Validation Tests"
echo "==================================="

# Set environment variables
export TEST_BASE_URL="https://calendar-assistant.example.com"
export TEST_NAMESPACE="production"
export GRAFANA_URL="https://grafana.example.com"
export PROMETHEUS_URL="https://prometheus.example.com"

# Install required packages
echo "📦 Installing required packages..."
pip install -r requirements-test.txt

# Run validation tests
echo "🧪 Running validation tests..."
python tests/phase4_validation.py

# Check test results
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "Phase 4 validation completed successfully."
else
    echo "❌ Some tests failed!"
    echo "Please check the test output for details."
    exit 1
fi

# Generate test report
echo "📊 Generating test report..."
python scripts/generate_test_report.py

echo "✨ Phase 4 validation completed!" 