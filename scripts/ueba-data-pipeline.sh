#!/bin/bash

# UEBA Complete Data Pipeline
# Consolidated script for all data generation, processing, and analytics
# Replaces: refresh-dashboard-data.sh, run-analytics.sh, run-advanced-ml.sh

set -e

echo "🎯 UEBA Complete Data Pipeline"
echo "=============================="
date
echo ""

# Configuration
VENV_PYTHON="/home/kunal/Documents/.venv/bin/python"
ANALYTICS_ENGINE="analytics-engine"

# Default parameters
DURATION=1
NORMAL_RATE=15
ATTACK_RATE=8
LOG_SIZE=50
ENABLE_ML=false
ENABLE_REPORTS=false

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --duration N        Data generation duration in minutes (default: 1)"
    echo "  --normal-rate N     Normal traffic rate per minute (default: 15)"
    echo "  --attack-rate N     Attack traffic rate per minute (default: 8)"
    echo "  --log-size N        Number of logs to parse (default: 50)"
    echo "  --enable-ml         Enable advanced ML analytics"
    echo "  --enable-reports    Enable detailed security reports"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Quick data refresh"
    echo "  $0 --duration 5 --enable-ml          # 5-min data with ML"
    echo "  $0 --enable-reports --log-size 100   # Detailed analysis"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --normal-rate)
            NORMAL_RATE="$2"
            shift 2
            ;;
        --attack-rate)
            ATTACK_RATE="$2"
            shift 2
            ;;
        --log-size)
            LOG_SIZE="$2"
            shift 2
            ;;
        --enable-ml)
            ENABLE_ML=true
            shift
            ;;
        --enable-reports)
            ENABLE_REPORTS=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Change to UEBA directory
cd /home/kunal/Documents/ueba-system

# Step 1: Generate dashboard-ready sample data with current timestamps
echo "🚀 Step 1: Generating dashboard-ready sample data..."
echo "   Adding ${NORMAL_RATE} normal + ${ATTACK_RATE} attack samples with current timestamps"

# Force index refresh first
curl -X POST "localhost:9200/nginx-parsed-logs/_refresh" >/dev/null 2>&1

# Generate sample data with precise current timestamps for immediate dashboard visibility
for i in $(seq 1 $NORMAL_RATE); do
    # Use current timestamp with small offsets for time series visualization
    timestamp=$(date -u -d "-$((i * 10)) seconds" --iso-8601=seconds | sed 's/+00:00/Z/')
    curl -X POST "localhost:9200/nginx-parsed-logs/_doc" -H "Content-Type: application/json" -d "{
        \"timestamp\":\"$timestamp\",
        \"@timestamp\":\"$timestamp\",
        \"ip\":\"192.168.1.$((100 + $i))\",
        \"method\":\"GET\",
        \"url\":\"/page$i\",
        \"status\":200,
        \"size\":$((1000 + RANDOM % 5000)),
        \"user_agent\":\"Mozilla/5.0 (Normal Traffic)\",
        \"risk_score\":$((RANDOM % 30))e-2,
        \"attack_type\":\"none\"
    }" >/dev/null 2>&1
done

for i in $(seq 1 $ATTACK_RATE); do
    # Use current timestamp with small offsets
    timestamp=$(date -u -d "-$((i * 15)) seconds" --iso-8601=seconds | sed 's/+00:00/Z/')
    attack_types=("sql_injection" "xss" "brute_force" "directory_traversal")
    attack_type=${attack_types[$((RANDOM % 4))]}
    curl -X POST "localhost:9200/nginx-parsed-logs/_doc" -H "Content-Type: application/json" -d "{
        \"timestamp\":\"$timestamp\",
        \"@timestamp\":\"$timestamp\",
        \"ip\":\"10.0.0.$((50 + $i))\",
        \"method\":\"POST\",
        \"url\":\"/admin/login\",
        \"status\":$((400 + RANDOM % 100)),
        \"size\":$((200 + RANDOM % 800)),
        \"user_agent\":\"curl/7.68.0 (Attack Tool)\",
        \"risk_score\":$((70 + RANDOM % 30))e-2,
        \"attack_type\":\"$attack_type\"
    }" >/dev/null 2>&1
done

# Force immediate index refresh for dashboard availability
curl -X POST "localhost:9200/nginx-parsed-logs/_refresh" >/dev/null 2>&1

echo ""
echo "📊 Step 2: Data successfully indexed with current timestamps..."

if [ "$ENABLE_REPORTS" = true ]; then
    echo ""
    echo "📊 Step 3: Parsing raw logs (size: $LOG_SIZE)..."
    $VENV_PYTHON $ANALYTICS_ENGINE/nginx_log_parser.py --size $LOG_SIZE

    echo ""
    echo "🛡️  Step 4: Generating security analytics..."
    $VENV_PYTHON $ANALYTICS_ENGINE/log_analytics.py --report
fi

if [ "$ENABLE_ML" = true ]; then
    echo ""
    echo "🤖 Step 5: Advanced ML Analytics..."
    
    # Check if system is running
    if ! ./ueba-manage.sh status | grep -q "Containers: Running"; then
        echo "⚠️  UEBA system not fully running. Please start system first."
        echo "   Run: ./ueba-manage.sh fresh"
        exit 1
    fi
    
    # Check data availability
    ELASTICSEARCH_HEALTH=$(curl -s http://localhost:9200/_cluster/health 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    
    if [ "$ELASTICSEARCH_HEALTH" != "green" ] && [ "$ELASTICSEARCH_HEALTH" != "yellow" ]; then
        echo "⚠️  Elasticsearch not healthy. Status: $ELASTICSEARCH_HEALTH"
        echo "   Skipping ML analysis"
    else
        echo "   🔍 Running anomaly detection..."
        $VENV_PYTHON $ANALYTICS_ENGINE/anomaly_detector.py
        
        echo "   📈 Running advanced behavioral analysis..."
        if [ -f "$ANALYTICS_ENGINE/advanced_behavioral_analysis.py" ]; then
            $VENV_PYTHON $ANALYTICS_ENGINE/advanced_behavioral_analysis.py
        fi
        
        echo "   🎯 Running threat detection..."
        if [ -f "$ANALYTICS_ENGINE/threat_detection.py" ]; then
            $VENV_PYTHON $ANALYTICS_ENGINE/threat_detection.py
        fi
    fi
fi

echo ""
echo "✅ UEBA Data Pipeline Completed Successfully!"
echo ""
echo "📊 Access points:"
echo "   • Grafana Dashboards: http://localhost:3000 (admin/admin)"
echo "   • Elasticsearch Data: http://localhost:9200/_search"
echo ""
echo "💡 Next steps:"
echo "   • View dashboards for real-time analytics"
echo "   • Run with --enable-ml for advanced detection"
echo "   • Use --enable-reports for detailed analysis"