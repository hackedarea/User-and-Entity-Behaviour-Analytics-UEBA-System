#!/bin/bash
echo "🔍 Pre-Deployment Field Validation"
echo "=================================="

cd /home/kunal/Documents/ueba-system/analytics-engine

# Run field validation
echo "1. Running field mapping validation..."
python3 field_mapping_validator.py

echo ""
echo "2. Checking Elasticsearch connectivity..."
curl -s localhost:9200/_cluster/health | grep -q "green\|yellow" && echo "✅ Elasticsearch healthy" || echo "❌ Elasticsearch unhealthy"

echo ""
echo "3. Verifying data availability..."
RECORD_COUNT=$(curl -s localhost:9200/nginx-parsed-logs/_count | grep -o '"count":[0-9]*' | cut -d: -f2)
echo "📊 Records available: $RECORD_COUNT"

if [ "$RECORD_COUNT" -gt 0 ]; then
    echo "✅ Data available for dashboard deployment"
    echo ""
    echo "🚀 Ready to deploy dashboards!"
    echo "Run: python3 grafana_dashboard_provisioner.py"
else
    echo "❌ No data available - run data generation first"
    echo "Run: ../ueba-manage.sh fresh_deployment"
fi
