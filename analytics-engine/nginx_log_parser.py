#!/usr/bin/env python3
"""
UEBA Log Parser - Nginx Log Processing Script
This script connects to Elasticsearch, retrieves raw Nginx logs,
parses them into structured fields, and stores the parsed data back.
"""

import re
import json
import requests
from datetime import datetime
from typing import Dict, Optional, List
import argparse
import sys

class NginxLogParser:
    def __init__(self, elasticsearch_url="http://localhost:9200"):
        self.es_url = elasticsearch_url
        self.session = requests.Session()
        
        # Nginx access log pattern (Combined Log Format)
        # Format: IP - - [timestamp] "method url protocol" status size "referer" "user_agent" "forwarded_for"
        self.access_log_pattern = re.compile(
            r'(?P<client_ip>\S+) - - \[(?P<timestamp>[^\]]+)\] '
            r'"(?P<method>\S+) (?P<url>\S+) (?P<protocol>[^"]+)" '
            r'(?P<status_code>\d+) (?P<response_size>\S+) '
            r'"(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)" "(?P<forwarded_for>[^"]*)"'
        )
        
        # Nginx error log pattern
        # Format: timestamp [level] pid#tid: *connection message, client: IP, server: server, request: "request", host: "host"
        self.error_log_pattern = re.compile(
            r'(?P<timestamp>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) '
            r'\[(?P<level>\w+)\] (?P<pid>\d+)#(?P<tid>\d+): '
            r'(?P<message>.*?)(?:, client: (?P<client_ip>\S+))?'
            r'(?:, server: (?P<server>[^,]+))?'
            r'(?:, request: "(?P<request>[^"]+)")?'
            r'(?:, host: "(?P<host>[^"]+)")?'
        )

    def test_connection(self) -> bool:
        """Test connection to Elasticsearch"""
        try:
            response = self.session.get(f"{self.es_url}/_cluster/health")
            response.raise_for_status()
            print(f"✅ Connected to Elasticsearch: {response.json()['status']}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Elasticsearch: {e}")
            return False

    def parse_access_log(self, message: str) -> Optional[Dict]:
        """Parse Nginx access log message"""
        match = self.access_log_pattern.match(message)
        if not match:
            return None
        
        parsed = match.groupdict()
        
        # Convert timestamp to ISO format
        try:
            dt = datetime.strptime(parsed['timestamp'], '%d/%b/%Y:%H:%M:%S %z')
            parsed['parsed_timestamp'] = dt.isoformat()
        except:
            parsed['parsed_timestamp'] = None
        
        # Convert numeric fields
        try:
            parsed['status_code'] = int(parsed['status_code'])
        except:
            parsed['status_code'] = 0
        
        try:
            parsed['response_size'] = int(parsed['response_size']) if parsed['response_size'] != '-' else 0
        except:
            parsed['response_size'] = 0
        
        # Extract URL components
        if '?' in parsed['url']:
            parsed['url_path'], parsed['url_query'] = parsed['url'].split('?', 1)
        else:
            parsed['url_path'] = parsed['url']
            parsed['url_query'] = None
        
        # Categorize status codes
        status = parsed['status_code']
        if 200 <= status < 300:
            parsed['status_category'] = 'success'
        elif 300 <= status < 400:
            parsed['status_category'] = 'redirect'
        elif 400 <= status < 500:
            parsed['status_category'] = 'client_error'
        elif 500 <= status < 600:
            parsed['status_category'] = 'server_error'
        else:
            parsed['status_category'] = 'unknown'
        
        # Add log type
        parsed['log_type'] = 'nginx_access'
        
        # Remove the raw timestamp field to avoid mapping conflicts
        if 'timestamp' in parsed:
            del parsed['timestamp']
        
        return parsed

    def parse_error_log(self, message: str) -> Optional[Dict]:
        """Parse Nginx error log message"""
        match = self.error_log_pattern.match(message)
        if not match:
            return None
        
        parsed = match.groupdict()
        
        # Convert timestamp to ISO format
        try:
            dt = datetime.strptime(parsed['timestamp'], '%Y/%m/%d %H:%M:%S')
            parsed['parsed_timestamp'] = dt.isoformat()
        except:
            parsed['parsed_timestamp'] = None
        
        # Convert numeric fields
        try:
            parsed['pid'] = int(parsed['pid'])
        except:
            parsed['pid'] = 0
        
        try:
            parsed['tid'] = int(parsed['tid'])
        except:
            parsed['tid'] = 0
        
        # Extract request method and URL from request field
        if parsed['request']:
            request_parts = parsed['request'].split(' ')
            if len(request_parts) >= 2:
                parsed['method'] = request_parts[0]
                parsed['url'] = request_parts[1]
                if len(request_parts) >= 3:
                    parsed['protocol'] = request_parts[2]
        
        # Add log type
        parsed['log_type'] = 'nginx_error'
        
        # Remove the raw timestamp field to avoid mapping conflicts
        if 'timestamp' in parsed:
            del parsed['timestamp']
        
        return parsed

    def get_raw_logs(self, index_pattern: str = "filebeat-8.19.4", size: int = 100) -> List[Dict]:
        """Retrieve raw logs from Elasticsearch"""
        query = {
            "size": size,
            "sort": [{"@timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [
                        {"exists": {"field": "message"}},
                        {"terms": {"logtype": ["nginx-access", "nginx-error"]}}
                    ]
                }
            },
            "_source": ["@timestamp", "message", "logtype", "host"]
        }
        
        try:
            response = self.session.post(
                f"{self.es_url}/{index_pattern}/_search",
                json=query,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            hits = response.json()["hits"]["hits"]
            print(f"📥 Retrieved {len(hits)} raw log entries")
            return hits
        
        except Exception as e:
            print(f"❌ Error retrieving logs: {e}")
            return []

    def parse_logs(self, raw_logs: List[Dict]) -> List[Dict]:
        """Parse raw log messages into structured data"""
        parsed_logs = []
        access_count = 0
        error_count = 0
        failed_count = 0
        
        for log_entry in raw_logs:
            source = log_entry["_source"]
            message = source["message"]
            logtype = source.get("logtype", "")
            
            parsed_data = None
            
            if logtype == "nginx-access":
                parsed_data = self.parse_access_log(message)
                if parsed_data:
                    access_count += 1
            elif logtype == "nginx-error":
                parsed_data = self.parse_error_log(message)
                if parsed_data:
                    error_count += 1
            
            if parsed_data:
                # Add original metadata
                parsed_data["original_timestamp"] = source["@timestamp"]
                parsed_data["original_message"] = message
                parsed_data["original_logtype"] = logtype
                parsed_data["host"] = source.get("host", {}).get("name", "unknown")
                parsed_data["document_id"] = log_entry["_id"]
                
                parsed_logs.append(parsed_data)
            else:
                failed_count += 1
        
        print(f"📊 Parsing results:")
        print(f"   - Access logs: {access_count}")
        print(f"   - Error logs: {error_count}")
        print(f"   - Failed to parse: {failed_count}")
        
        return parsed_logs

    def create_parsed_index(self, index_name: str = "nginx-parsed-logs"):
        """Create index for parsed logs with proper mapping"""
        mapping = {
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "original_timestamp": {"type": "date"},
                    "parsed_timestamp": {"type": "date"},
                    "log_type": {"type": "keyword"},
                    "client_ip": {"type": "ip"},
                    "method": {"type": "keyword"},
                    "url": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "url_path": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "url_query": {"type": "text"},
                    "protocol": {"type": "keyword"},
                    "status_code": {"type": "integer"},
                    "status_category": {"type": "keyword"},
                    "response_size": {"type": "long"},
                    "referer": {"type": "text"},
                    "user_agent": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "forwarded_for": {"type": "text"},
                    "level": {"type": "keyword"},
                    "message": {"type": "text"},
                    "server": {"type": "keyword"},
                    "host": {"type": "keyword"},
                    "original_message": {"type": "text"},
                    "original_logtype": {"type": "keyword"}
                }
            }
        }
        
        try:
            response = self.session.put(
                f"{self.es_url}/{index_name}",
                json=mapping,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✅ Index '{index_name}' already exists")
            elif response.status_code == 201:
                print(f"✅ Created new index '{index_name}'")
            else:
                print(f"⚠️  Index creation response: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Error creating index: {e}")

    def store_parsed_logs(self, parsed_logs: List[Dict], index_name: str = "nginx-parsed-logs"):
        """Store parsed logs in Elasticsearch"""
        if not parsed_logs:
            print("📝 No parsed logs to store")
            return
        
        # Prepare bulk request
        bulk_data = []
        for log in parsed_logs:
            # Index action
            bulk_data.append(json.dumps({"index": {"_index": index_name}}))
            # Document data
            log_copy = log.copy()
            log_copy["@timestamp"] = datetime.now().isoformat()
            bulk_data.append(json.dumps(log_copy))
        
        bulk_request = "\n".join(bulk_data) + "\n"
        
        try:
            response = self.session.post(
                f"{self.es_url}/_bulk",
                data=bulk_request,
                headers={"Content-Type": "application/x-ndjson"}
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("errors"):
                print(f"⚠️  Some documents failed to index")
                for item in result["items"]:
                    if "error" in item.get("index", {}):
                        print(f"   Error: {item['index']['error']}")
            else:
                print(f"✅ Successfully stored {len(parsed_logs)} parsed logs in '{index_name}'")
        
        except Exception as e:
            print(f"❌ Error storing parsed logs: {e}")

    def show_sample_parsed_data(self, parsed_logs: List[Dict], count: int = 3):
        """Display sample parsed data"""
        if not parsed_logs:
            return
        
        print(f"\n📋 Sample Parsed Data (showing {min(count, len(parsed_logs))} entries):")
        print("=" * 80)
        
        for i, log in enumerate(parsed_logs[:count]):
            print(f"\n🔍 Entry {i+1} ({log.get('log_type', 'unknown')}):")
            
            if log.get('log_type') == 'nginx_access':
                print(f"   Client IP: {log.get('client_ip', 'N/A')}")
                print(f"   Method: {log.get('method', 'N/A')}")
                print(f"   URL: {log.get('url', 'N/A')}")
                print(f"   Status: {log.get('status_code', 'N/A')} ({log.get('status_category', 'N/A')})")
                print(f"   Size: {log.get('response_size', 'N/A')} bytes")
                print(f"   User Agent: {log.get('user_agent', 'N/A')[:50]}...")
                
            elif log.get('log_type') == 'nginx_error':
                print(f"   Client IP: {log.get('client_ip', 'N/A')}")
                print(f"   Level: {log.get('level', 'N/A')}")
                print(f"   Message: {log.get('message', 'N/A')[:100]}...")
                print(f"   Request: {log.get('request', 'N/A')}")
                print(f"   Server: {log.get('server', 'N/A')}")
            
            print(f"   Timestamp: {log.get('parsed_timestamp', 'N/A')}")

def main():
    parser = argparse.ArgumentParser(description="Parse Nginx logs from Elasticsearch")
    parser.add_argument("--es-url", default="http://localhost:9200", 
                       help="Elasticsearch URL (default: http://localhost:9200)")
    parser.add_argument("--size", type=int, default=100, 
                       help="Number of logs to process (default: 100)")
    parser.add_argument("--index", default="nginx-parsed-logs", 
                       help="Index name for parsed logs (default: nginx-parsed-logs)")
    parser.add_argument("--sample-only", action="store_true", 
                       help="Only show sample parsed data, don't store in Elasticsearch")
    
    args = parser.parse_args()
    
    print("🚀 Starting Nginx Log Parser")
    print(f"   Elasticsearch: {args.es_url}")
    print(f"   Processing: {args.size} logs")
    print(f"   Target index: {args.index}")
    print()
    
    # Initialize parser
    parser = NginxLogParser(args.es_url)
    
    # Test connection
    if not parser.test_connection():
        sys.exit(1)
    
    # Get raw logs
    print("\n📥 Retrieving raw logs...")
    raw_logs = parser.get_raw_logs(size=args.size)
    
    if not raw_logs:
        print("❌ No logs found to process")
        sys.exit(1)
    
    # Parse logs
    print("\n🔧 Parsing logs...")
    parsed_logs = parser.parse_logs(raw_logs)
    
    if not parsed_logs:
        print("❌ No logs could be parsed")
        sys.exit(1)
    
    # Show sample data
    parser.show_sample_parsed_data(parsed_logs)
    
    if not args.sample_only:
        # Create index for parsed logs
        print(f"\n📝 Creating/checking index '{args.index}'...")
        parser.create_parsed_index(args.index)
        
        # Store parsed logs
        print(f"\n💾 Storing parsed logs...")
        parser.store_parsed_logs(parsed_logs, args.index)
        
        print(f"\n✅ Log parsing completed!")
        print(f"   Check your parsed data: curl 'http://localhost:9200/{args.index}/_search?pretty&size=2'")
    else:
        print(f"\n✅ Sample parsing completed (not stored)")

if __name__ == "__main__":
    main()