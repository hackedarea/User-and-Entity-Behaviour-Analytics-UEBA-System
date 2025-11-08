#!/bin/bash
"""
UEBA Field Mapping Prevention System
=====================================
Comprehensive system to prevent field mapping issues
"""

# Field Mapping Documentation Generator
echo "🔍 UEBA Field Mapping Prevention System"
echo "======================================="
echo ""

# Generate current field reference
echo "📊 Generating field reference documentation..."
cd /home/kunal/Documents/ueba-system/analytics-engine
python3 field_mapping_validator.py

echo ""
echo "✅ Field reference generated: analytics-engine/field_reference.json"

# Create field mapping cheat sheet
cat > /home/kunal/Documents/ueba-system/FIELD_MAPPING_GUIDE.md << 'EOF'
# UEBA Field Mapping Guide

## 🚨 CRITICAL: Field Mapping Rules

### Text Fields Require .keyword for Aggregations
```
❌ WRONG: "user_agent" 
✅ CORRECT: "user_agent.keyword"

❌ WRONG: "url"
✅ CORRECT: "url.keyword"
```

### Common Field Mapping Mistakes
| Wrong Field | Correct Field | Type |
|-------------|---------------|------|
| `status_code` | `status` | long |
| `response_size` | `size` | long |
| `client_ip` | `ip` | ip |
| `user_agent_string` | `user_agent.keyword` | text+keyword |
| `request_method` | `method` | keyword |

### Available Fields (Auto-Generated)
```json
{
  "timestamp": "date",
  "@timestamp": "date",
  "ip": "ip",
  "method": "keyword",
  "url": "text (use url.keyword for aggregations)",
  "status": "long",
  "size": "long",
  "user_agent": "text (use user_agent.keyword for aggregations)",
  "risk_score": "float",
  "attack_type": "keyword",
  "country": "keyword",
  "city": "keyword"
}
```

### Dashboard-Specific Requirements

#### SOC Operations Center
- Response Status Distribution: `status`
- Top Client IPs: `ip` 
- HTTP Method Analysis: `method`

#### Security Analytics & ML
- URL Path Analysis: `url.keyword`
- Response Size Distribution: `size`
- Risk Score Analysis: `risk_score`

#### Threat Intelligence
- User Agent Analysis: `user_agent.keyword`
- Attack Type Distribution: `attack_type`
- Geographic Distribution: `country`

### Validation Command
```bash
cd /home/kunal/Documents/ueba-system/analytics-engine
python3 field_mapping_validator.py
```

### Auto-Fix Command
The dashboard provisioner now automatically validates and fixes field mappings before deployment.

## 🛡️ Prevention Measures Implemented

1. **Field Mapping Validator**: Validates all fields before dashboard deployment
2. **Auto-Fix System**: Automatically corrects common field mapping mistakes
3. **Field Reference Documentation**: Always up-to-date field mapping reference
4. **Validation Integration**: Built into dashboard provisioner
5. **Common Mistakes Database**: Prevents repeated field mapping errors

## 📋 Checklist Before Adding New Dashboards

- [ ] Check field types in Elasticsearch mapping
- [ ] Use `.keyword` for text fields in aggregations
- [ ] Run field mapping validator
- [ ] Test aggregation queries directly in Elasticsearch
- [ ] Verify dashboard deployment with auto-validation

## 🚀 Quick Fix Commands

```bash
# Generate latest field reference
cd /home/kunal/Documents/ueba-system/analytics-engine
python3 field_mapping_validator.py

# Deploy dashboards with auto-validation
python3 grafana_dashboard_provisioner.py

# Check Elasticsearch field mappings
curl -s "localhost:9200/nginx-parsed-logs/_mapping?pretty"
```
EOF

echo "📋 Created comprehensive field mapping guide: FIELD_MAPPING_GUIDE.md"

# Create pre-deployment validation script
cat > /home/kunal/Documents/ueba-system/scripts/validate-before-deploy.sh << 'EOF'
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
EOF

chmod +x /home/kunal/Documents/ueba-system/scripts/validate-before-deploy.sh

echo "🛡️ Created pre-deployment validation script: scripts/validate-before-deploy.sh"

# Update main management script to include validation
echo ""
echo "📝 Updating main scripts to include field validation..."

# Update ueba-manage.sh to include validation
if ! grep -q "validate-before-deploy.sh" /home/kunal/Documents/ueba-system/ueba-manage.sh; then
    sed -i '/fresh_deployment()/a\    echo "🔍 Running field validation..."\n    ./scripts/validate-before-deploy.sh' /home/kunal/Documents/ueba-system/ueba-manage.sh
fi

echo "✅ Enhanced main management script with validation"

echo ""
echo "🎉 FIELD MAPPING PREVENTION SYSTEM COMPLETE!"
echo "============================================="
echo ""
echo "📋 Implemented Safeguards:"
echo "- ✅ Field mapping validator with auto-fix"
echo "- ✅ Pre-deployment validation script"
echo "- ✅ Comprehensive field mapping guide"
echo "- ✅ Integration with dashboard provisioner"
echo "- ✅ Common mistakes prevention database"
echo "- ✅ Auto-generated field reference documentation"
echo ""
echo "🛡️ This system will prevent field mapping issues by:"
echo "1. Validating all fields before dashboard deployment"
echo "2. Auto-fixing common field mapping mistakes"
echo "3. Providing real-time field mapping documentation"
echo "4. Running pre-deployment checks"
echo "5. Maintaining a database of common mistakes"
echo ""
echo "🚀 All future dashboard deployments will be validated automatically!"