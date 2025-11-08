#!/bin/bash

# UEBA Complete Analytics Pipeline
# Run the complete data processing and analytics pipeline

echo "🔍 UEBA Complete Analytics Pipeline"
echo "===================================="

echo ""
echo "📊 Step 1: Parsing raw logs..."
/home/kunal/Documents/.venv/bin/python analytics-engine/nginx_log_parser.py --size 50

echo ""
echo "🛡️  Step 2: Generating security analytics..."
/home/kunal/Documents/.venv/bin/python analytics-engine/log_analytics.py --report

echo ""
echo "🤖 Step 3: Preparing ML features..."
/home/kunal/Documents/.venv/bin/python analytics-engine/anomaly_detector.py

echo ""
echo "✅ Complete analytics pipeline finished!"
echo "📈 Check the output above for security insights and ML-ready data."