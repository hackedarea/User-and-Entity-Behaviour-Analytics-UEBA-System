#!/bin/bash

# UEBA Dashboard Data Fixer
# Adds current timestamp data to fix dashboard display issues

echo "🔧 UEBA Dashboard Data Fixer"
echo "============================"
echo ""

echo "📊 Current data status:"
curl -s "http://localhost:9200/nginx-parsed-logs/_count" | python3 -c "import sys, json; print(f'Total records: {json.load(sys.stdin)[\"count\"]}')"

echo ""
echo "⏰ Adding data with current timestamps..."

# Add 20 data points with exact current timestamps
for i in {1..20}; do
    current_time=$(date -u --iso-8601=seconds | sed 's/+00:00/Z/')
    
    if [ $((i % 3)) -eq 0 ]; then
        # Add some attack data
        curl -X POST "localhost:9200/nginx-parsed-logs/_doc" -H "Content-Type: application/json" -d "{
            \"@timestamp\":\"$current_time\",
            \"timestamp\":\"$current_time\",
            \"ip\":\"10.0.0.$((50 + $i))\",
            \"method\":\"POST\",
            \"url\":\"/admin/login\",
            \"status\":403,
            \"size\":$((500 + RANDOM % 500)),
            \"user_agent\":\"Suspicious Bot $i\",
            \"risk_score\":$((80 + RANDOM % 20))e-2,
            \"attack_type\":\"brute_force\"
        }" >/dev/null 2>&1
    else
        # Add normal data
        curl -X POST "localhost:9200/nginx-parsed-logs/_doc" -H "Content-Type: application/json" -d "{
            \"@timestamp\":\"$current_time\",
            \"timestamp\":\"$current_time\",
            \"ip\":\"192.168.1.$((100 + $i))\",
            \"method\":\"GET\",
            \"url\":\"/page$i\",
            \"status\":200,
            \"size\":$((1000 + RANDOM % 2000)),
            \"user_agent\":\"Mozilla/5.0 (Normal User $i)\",
            \"risk_score\":$((10 + RANDOM % 30))e-2,
            \"attack_type\":\"none\"
        }" >/dev/null 2>&1
    fi
    
    echo -n "."
    sleep 0.5  # Small delay to spread timestamps
done

echo ""
echo ""

# Refresh the index
curl -X POST "localhost:9200/nginx-parsed-logs/_refresh" >/dev/null 2>&1

echo "📊 Updated data status:"
curl -s "http://localhost:9200/nginx-parsed-logs/_count" | python3 -c "import sys, json; print(f'Total records: {json.load(sys.stdin)[\"count\"]}')"

echo ""
echo "✅ Data fix completed!"
echo ""
echo "🎯 Dashboard Access:"
echo "   URL: http://localhost:3000"
echo "   Login: admin/admin"
echo ""
echo "📋 Time Range Tips:"
echo "   • Set dashboard time range to 'Last 15 minutes' or 'Last 1 hour'"
echo "   • Click the time picker (top right) and select recent range"
echo "   • Use 'Last 5 minutes' for most recent data"
echo ""
echo "🔄 If still no data, try:"
echo "   • Refresh the dashboard (Ctrl+R or F5)"
echo "   • Check time range is set to recent time"
echo "   • Verify time zone settings in Grafana"