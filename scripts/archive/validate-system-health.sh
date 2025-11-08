#!/bin/bash

# UEBA System Health Validation Script
# =====================================
# Ensures system is ready before dashboard deployment
# Prevents common restart issues

echo "🔍 UEBA System Health Validation"
echo "================================"

# Function to check service health
check_service_health() {
    local service=$1
    local url=$2
    local timeout=${3:-10}
    
    echo -n "📡 Checking $service... "
    
    if curl -s --max-time $timeout "$url" > /dev/null 2>&1; then
        echo "✅ OK"
        return 0
    else
        echo "❌ FAILED"
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=${3:-30}
    local sleep_time=${4:-2}
    
    echo "⏳ Waiting for $service to be ready..."
    
    for i in $(seq 1 $max_attempts); do
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            echo "✅ $service is ready!"
            return 0
        fi
        echo "   Attempt $i/$max_attempts - waiting ${sleep_time}s..."
        sleep $sleep_time
    done
    
    echo "❌ $service failed to become ready after $((max_attempts * sleep_time)) seconds"
    return 1
}

# Check if Docker containers are running
echo ""
echo "🐳 Checking Docker containers..."
if ! docker ps | grep -q "es-node1"; then
    echo "❌ Elasticsearch container not running"
    exit 1
fi

if ! docker ps | grep -q "grafana"; then
    echo "❌ Grafana container not running"
    exit 1
fi

echo "✅ All required containers are running"

# Wait for services to be ready
echo ""
echo "🚀 Waiting for services to initialize..."

# Wait for Elasticsearch
if ! wait_for_service "Elasticsearch" "http://localhost:9200/_cluster/health" 30 3; then
    exit 1
fi

# Wait for Grafana
if ! wait_for_service "Grafana" "http://localhost:3000/api/health" 30 3; then
    exit 1
fi

# Check Elasticsearch data
echo ""
echo "📊 Checking data availability..."
DATA_COUNT=$(curl -s "http://localhost:9200/nginx-parsed-logs/_count" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('count', 0))" 2>/dev/null || echo "0")

if [ "$DATA_COUNT" -gt 0 ]; then
    echo "✅ Found $DATA_COUNT records in nginx-parsed-logs index"
else
    echo "⚠️  No data found - generating fresh data..."
    cd /home/kunal/Documents/ueba-system
    python3 analytics-engine/direct_log_processor.py --generate-samples
    echo "✅ Fresh data generated"
fi

# Validate network connectivity between containers
echo ""
echo "🌐 Validating container network connectivity..."

# Get container IPs
ES_IP=$(docker inspect es-node1 | grep '"IPAddress"' | grep -v '""' | head -1 | cut -d'"' -f4)
GRAFANA_IP=$(docker inspect grafana | grep '"IPAddress"' | grep -v '""' | head -1 | cut -d'"' -f4)

if [ -n "$ES_IP" ] && [ -n "$GRAFANA_IP" ]; then
    echo "✅ Elasticsearch IP: $ES_IP"
    echo "✅ Grafana IP: $GRAFANA_IP"
    
    # Test connectivity from Grafana to Elasticsearch
    if docker exec grafana curl -s --max-time 5 "http://$ES_IP:9200/_cluster/health" > /dev/null 2>&1; then
        echo "✅ Network connectivity verified"
    else
        echo "❌ Network connectivity issue detected"
        exit 1
    fi
else
    echo "❌ Could not determine container IPs"
    exit 1
fi

echo ""
echo "🎉 System Health Validation Complete!"
echo "✅ All systems are ready for dashboard deployment"
echo ""