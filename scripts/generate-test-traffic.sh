#!/bin/bash

# Generate Test Traffic for UEBA System
# This script generates various types of web traffic to create realistic log data

echo "🚦 Generating test traffic for UEBA system..."

# Check if a custom URL is provided, otherwise use default
BASE_URL="${1:-http://localhost:80}"

# Check if the target URL is accessible
echo "🔍 Testing connection to $BASE_URL..."
if ! curl -s --max-time 5 "$BASE_URL" >/dev/null 2>&1; then
    echo "⚠️  Warning: Cannot connect to $BASE_URL"
    echo "   This script generates HTTP traffic for testing purposes."
    echo "   Make sure your web server is running or provide a different URL."
    echo ""
    echo "Usage: $0 [URL]"
    echo "Example: $0 http://httpbin.org"
    echo ""
    echo "Note: For UEBA testing, you can still use the data pipeline:"
    echo "      ./ueba-data-pipeline.sh"
    exit 1
fi

echo "✅ Connection successful to $BASE_URL"

# Function to generate random traffic
generate_traffic() {
    echo "📊 Generating $1 requests..."
    
    # Normal requests
    for i in $(seq 1 $1); do
        # Mix of different request types
        case $((i % 7)) in
            0) curl -s "$BASE_URL/" > /dev/null ;;
            1) curl -s "$BASE_URL/api/users" > /dev/null ;;
            2) curl -s "$BASE_URL/dashboard" > /dev/null ;;
            3) curl -s "$BASE_URL/login" > /dev/null ;;
            4) curl -s "$BASE_URL/static/css/style.css" > /dev/null ;;
            5) curl -s "$BASE_URL/images/logo.png" > /dev/null ;;
            6) curl -s "$BASE_URL/404-page" > /dev/null ;;
        esac
        
        # Add some delay to simulate realistic traffic
        sleep 0.1
    done
}

# Function to simulate suspicious activity
generate_suspicious_traffic() {
    echo "🚨 Generating suspicious traffic patterns..."
    
    # Rapid requests (potential DoS)
    for i in {1..10}; do
        curl -s "$BASE_URL/admin" > /dev/null &
    done
    wait
    
    # SQL injection attempts
    curl -s "$BASE_URL/login?user=admin'OR'1'='1" > /dev/null
    curl -s "$BASE_URL/search?q=';DROP TABLE users;--" > /dev/null
    
    # Directory traversal attempts
    curl -s "$BASE_URL/../../../etc/passwd" > /dev/null
    curl -s "$BASE_URL/admin/../../config" > /dev/null
    
    # Scanner-like behavior
    for path in admin config backup .env robots.txt sitemap.xml; do
        curl -s "$BASE_URL/$path" > /dev/null
        sleep 0.1
    done
}

# Function to simulate different user agents
generate_mixed_user_agents() {
    echo "🤖 Generating traffic with different user agents..."
    
    user_agents=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        "Googlebot/2.1 (+http://www.google.com/bot.html)"
        "facebookexternalhit/1.1"
        "Baiduspider+(+http://www.baidu.com/search/spider.htm)"
        "python-requests/2.28.1"
    )
    
    for i in {1..14}; do
        ua=${user_agents[$((i % ${#user_agents[@]}))]}
        curl -s -H "User-Agent: $ua" "$BASE_URL/" > /dev/null
        sleep 0.2
    done
}

# Main execution
echo "Starting traffic generation..."
echo

# Generate normal traffic
generate_traffic 20

echo

# Generate mixed user agent traffic
generate_mixed_user_agents

echo

# Generate some suspicious patterns
generate_suspicious_traffic

echo
echo "✅ Traffic generation completed!"
echo "📊 Check logs with: tail -f /var/log/nginx_from_container/access.log"
echo "🔍 Run analytics with: python3 log_analytics.py --report"