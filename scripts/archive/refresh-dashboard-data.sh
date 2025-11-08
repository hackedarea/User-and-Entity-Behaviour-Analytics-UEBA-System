#!/bin/bash

# UEBA Dashboard Data Automation
# Generates traffic and processes logs automatically

echo "🎯 UEBA Dashboard Data Automation"
echo "================================="
date

cd /home/kunal/Documents/ueba-system

echo ""
echo "🚀 Step 1: Generating fresh traffic data..."
/home/kunal/Documents/.venv/bin/python analytics-engine/realtime_data_streamer.py --duration 1 --normal-rate 15 --attack-rate 8

echo ""
echo "📊 Step 2: Processing logs to Elasticsearch..."
/home/kunal/Documents/.venv/bin/python analytics-engine/direct_log_processor.py

echo ""
echo "📈 Step 3: Checking data count..."
echo "Total documents in nginx-parsed-logs:"
curl -s http://localhost:9200/nginx-parsed-logs/_count | python3 -c "import json,sys; print(json.load(sys.stdin)['count'])"

echo ""
echo "✅ Data refresh completed!"
echo "🌐 Access your dashboards:"
echo "   • SOC Dashboard: http://localhost:3000/d/f2b00f58-14de-488b-8f48-6b7ad2b0165e"
echo "   • ML Analytics: http://localhost:3000/d/ebdac9eb-4b6e-4eb0-b7ea-97484f95ddb5"  
echo "   • Executive Summary: http://localhost:3000/d/9a36c139-7e4e-48c7-9662-c5d6e59d6c90"
echo ""
echo "🔑 Login: admin / 7985"
echo "⏰ Last updated: $(date)"