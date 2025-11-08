#!/bin/bash

# UEBA Advanced ML Analysis Runner
# Comprehensive script to run advanced machine learning anomaly detection

echo "🤖 UEBA Advanced ML Anomaly Detection"
echo "====================================="

# Check if system is running
echo "🔍 Checking system status..."
if ! ./system-management/check-ueba-status.sh | grep -q "All services are running"; then
    echo "⚠️  UEBA system not fully running. Starting system first..."
    ./start-system.sh
    sleep 10
fi

# Check if we have data
echo ""
echo "📊 Checking for data availability..."
ELASTICSEARCH_HEALTH=$(curl -s http://localhost:9200/_cluster/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$ELASTICSEARCH_HEALTH" != "green" ] && [ "$ELASTICSEARCH_HEALTH" != "yellow" ]; then
    echo "❌ Elasticsearch not available. Please ensure the system is running."
    exit 1
fi

# Parse latest logs if needed
echo ""
echo "🔧 Ensuring fresh parsed data..."
/home/kunal/Documents/.venv/bin/python analytics-engine/nginx_log_parser.py --size 100

# Run advanced ML analysis
echo ""
echo "🚀 Running Advanced ML Anomaly Detection..."
echo "============================================"

# Run with different configurations
echo ""
echo "📈 Analysis 1: Standard Configuration"
/home/kunal/Documents/.venv/bin/python analytics-engine/advanced_ml_detector.py --size 100 --contamination 0.1

echo ""
echo "📈 Analysis 2: High Sensitivity (more anomalies)"
/home/kunal/Documents/.venv/bin/python analytics-engine/advanced_ml_detector.py --size 100 --contamination 0.2

echo ""
echo "📈 Analysis 3: Low Sensitivity (fewer anomalies)"  
/home/kunal/Documents/.venv/bin/python analytics-engine/advanced_ml_detector.py --size 100 --contamination 0.05

echo ""
echo "✅ Advanced ML Analysis Complete!"
echo "================================"
echo ""
echo "📋 Results Summary:"
echo "   • Multiple ML algorithms applied (Isolation Forest, One-Class SVM, LOF, DBSCAN)"
echo "   • Ensemble scoring for improved accuracy"
echo "   • Trained models saved to ml_models/ directory"
echo "   • Detailed security insights provided"
echo ""
echo "💡 Next Steps:"
echo "   • Review the detailed reports above"
echo "   • Check ml_models/ directory for saved models"
echo "   • Consider implementing real-time scoring"
echo "   • Set up automated alerting for high-risk anomalies"