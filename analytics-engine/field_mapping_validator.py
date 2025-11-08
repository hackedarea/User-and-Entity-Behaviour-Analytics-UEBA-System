#!/usr/bin/env python3
"""
UEBA Field Mapping Validator
============================
Prevents dashboard field mapping issues by validating Elasticsearch field mappings
against dashboard configurations before deployment.

Author: UEBA System
Date: 2025-10-05
"""

import json
import requests
from typing import Dict, List, Tuple, Any
from datetime import datetime

class FieldMappingValidator:
    def __init__(self, es_url: str = "http://localhost:9200", index_name: str = "nginx-parsed-logs"):
        self.es_url = es_url
        self.index_name = index_name
        self.field_mappings = {}
        self.validation_rules = {}
        self.load_field_mappings()
        self.setup_validation_rules()
    
    def load_field_mappings(self) -> bool:
        """Load current field mappings from Elasticsearch"""
        try:
            response = requests.get(f"{self.es_url}/{self.index_name}/_mapping")
            if response.status_code == 200:
                mappings = response.json()
                self.field_mappings = mappings[self.index_name]["mappings"]["properties"]
                print(f"✅ Loaded field mappings for {self.index_name}")
                return True
            else:
                print(f"❌ Failed to load field mappings: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error loading field mappings: {e}")
            return False
    
    def setup_validation_rules(self):
        """Setup field validation rules based on common dashboard requirements"""
        self.validation_rules = {
            # Text fields need .keyword for aggregations
            "aggregation_fields": {
                "user_agent": "user_agent.keyword",
                "url": "url.keyword",
                "method": "method",  # Already keyword
                "status": "status",  # Already numeric
                "ip": "ip",  # Already ip type
                "attack_type": "attack_type",  # Already keyword
                "country": "country",  # Already keyword
                "city": "city",  # Already keyword
                "size": "size",  # Already numeric
                "risk_score": "risk_score",  # Already numeric
                "@timestamp": "@timestamp",  # Already date
                "timestamp": "timestamp"  # Already date
            },
            
            # Common field mapping mistakes
            "common_mistakes": {
                "status_code": "status",
                "response_size": "size",
                "client_ip": "ip",
                "user_agent_string": "user_agent.keyword",
                "request_method": "method",
                "response_status": "status"
            },
            
            # Required fields for each dashboard
            "dashboard_requirements": {
                "soc_operations": ["status", "ip", "method", "url.keyword", "user_agent.keyword"],
                "security_analytics": ["size", "url.keyword", "status", "risk_score", "method"],
                "threat_intelligence": ["user_agent.keyword", "attack_type", "risk_score", "country"],
                "executive_summary": ["@timestamp", "status", "risk_score"]
            }
        }
    
    def validate_field(self, field_name: str) -> Tuple[bool, str, str]:
        """
        Validate a single field name against mappings
        Returns: (is_valid, corrected_field, message)
        """
        # Check if field exists as-is
        if field_name in self.field_mappings:
            field_type = self.field_mappings[field_name].get("type", "unknown")
            
            # If it's a text field being used for aggregation, suggest .keyword
            if field_type == "text" and "keyword" in self.field_mappings[field_name].get("fields", {}):
                return False, f"{field_name}.keyword", f"Text field '{field_name}' should use '.keyword' for aggregations"
            
            return True, field_name, f"Field '{field_name}' is valid ({field_type})"
        
        # Check for common mistakes
        if field_name in self.validation_rules["common_mistakes"]:
            correct_field = self.validation_rules["common_mistakes"][field_name]
            return False, correct_field, f"Common mistake: '{field_name}' should be '{correct_field}'"
        
        # Check if .keyword version exists
        base_field = field_name.replace(".keyword", "")
        if base_field in self.field_mappings:
            field_info = self.field_mappings[base_field]
            if field_info.get("type") == "text" and "keyword" in field_info.get("fields", {}):
                return True, f"{base_field}.keyword", f"Using keyword field for '{base_field}'"
        
        return False, field_name, f"Field '{field_name}' not found in mapping"
    
    def validate_dashboard_config(self, dashboard_config: Dict) -> Dict[str, Any]:
        """Validate entire dashboard configuration"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "corrections": [],
            "timestamp": datetime.now().isoformat()
        }
        
        def extract_fields_from_targets(targets: List[Dict]) -> List[str]:
            """Extract field names from dashboard targets"""
            fields = []
            for target in targets:
                # Extract from bucketAggs
                for agg in target.get("bucketAggs", []):
                    if "field" in agg:
                        fields.append(agg["field"])
                
                # Extract from metrics
                for metric in target.get("metrics", []):
                    if "field" in metric:
                        fields.append(metric["field"])
            
            return fields
        
        # Validate each panel
        for panel in dashboard_config.get("dashboard", {}).get("panels", []):
            panel_id = panel.get("id", "unknown")
            panel_title = panel.get("title", "unknown")
            
            # Extract fields from targets
            fields = extract_fields_from_targets(panel.get("targets", []))
            
            for field in fields:
                is_valid, corrected_field, message = self.validate_field(field)
                
                if not is_valid:
                    validation_results["valid"] = False
                    validation_results["errors"].append({
                        "panel_id": panel_id,
                        "panel_title": panel_title,
                        "field": field,
                        "corrected_field": corrected_field,
                        "message": message
                    })
                    validation_results["corrections"].append({
                        "original": field,
                        "corrected": corrected_field
                    })
                else:
                    if "should use" in message:
                        validation_results["warnings"].append({
                            "panel_id": panel_id,
                            "panel_title": panel_title,
                            "field": field,
                            "message": message
                        })
        
        return validation_results
    
    def auto_fix_dashboard_config(self, dashboard_config: Dict) -> Dict:
        """Automatically fix field mappings in dashboard configuration"""
        def fix_targets(targets: List[Dict]) -> List[Dict]:
            """Fix field names in targets"""
            for target in targets:
                # Fix bucketAggs
                for agg in target.get("bucketAggs", []):
                    if "field" in agg:
                        is_valid, corrected_field, _ = self.validate_field(agg["field"])
                        if not is_valid:
                            print(f"🔧 Auto-fixing field: {agg['field']} → {corrected_field}")
                            agg["field"] = corrected_field
                
                # Fix metrics
                for metric in target.get("metrics", []):
                    if "field" in metric:
                        is_valid, corrected_field, _ = self.validate_field(metric["field"])
                        if not is_valid:
                            print(f"🔧 Auto-fixing metric field: {metric['field']} → {corrected_field}")
                            metric["field"] = corrected_field
            
            return targets
        
        # Fix each panel
        for panel in dashboard_config.get("dashboard", {}).get("panels", []):
            if "targets" in panel:
                panel["targets"] = fix_targets(panel["targets"])
        
        return dashboard_config
    
    def generate_field_reference(self) -> Dict[str, Any]:
        """Generate field reference documentation"""
        reference = {
            "index_name": self.index_name,
            "generated_at": datetime.now().isoformat(),
            "field_mappings": {},
            "aggregation_ready_fields": [],
            "common_corrections": self.validation_rules["common_mistakes"],
            "dashboard_requirements": self.validation_rules["dashboard_requirements"]
        }
        
        for field_name, field_info in self.field_mappings.items():
            field_type = field_info.get("type", "unknown")
            reference["field_mappings"][field_name] = {
                "type": field_type,
                "aggregation_field": field_name if field_type in ["keyword", "long", "float", "date", "ip"] else f"{field_name}.keyword" if field_info.get("fields", {}).get("keyword") else None
            }
            
            # Add to aggregation ready fields
            if field_type in ["keyword", "long", "float", "date", "ip"]:
                reference["aggregation_ready_fields"].append(field_name)
            elif field_info.get("fields", {}).get("keyword"):
                reference["aggregation_ready_fields"].append(f"{field_name}.keyword")
        
        return reference
    
    def print_validation_report(self, validation_results: Dict):
        """Print formatted validation report"""
        print("\n" + "="*60)
        print("🔍 FIELD MAPPING VALIDATION REPORT")
        print("="*60)
        
        if validation_results["valid"]:
            print("✅ All field mappings are VALID!")
        else:
            print("❌ Found field mapping issues:")
            
            for error in validation_results["errors"]:
                print(f"\n🚨 Panel: {error['panel_title']} (ID: {error['panel_id']})")
                print(f"   Field: {error['field']}")
                print(f"   Fix: {error['corrected_field']}")
                print(f"   Reason: {error['message']}")
        
        if validation_results["warnings"]:
            print("\n⚠️ Warnings:")
            for warning in validation_results["warnings"]:
                print(f"   {warning['panel_title']}: {warning['message']}")
        
        print(f"\n📅 Validation completed: {validation_results['timestamp']}")
        print("="*60)

def main():
    """Main validation function"""
    print("🚀 UEBA Field Mapping Validator")
    print("================================")
    
    validator = FieldMappingValidator()
    
    # Generate and save field reference
    reference = validator.generate_field_reference()
    with open("/home/kunal/Documents/ueba-system/analytics-engine/field_reference.json", "w") as f:
        json.dump(reference, f, indent=2)
    
    print("✅ Generated field reference documentation")
    print("📁 Saved to: analytics-engine/field_reference.json")
    
    return validator

if __name__ == "__main__":
    main()