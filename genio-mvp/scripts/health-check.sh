#!/bin/bash
# Health check script for monitoring (T073)

API_URL=${1:-"http://localhost:8000"}
ALERT_WEBHOOK=${2:-""}

echo "Checking health at $API_URL..."

# Check health endpoint
HEALTH=$(curl -sf "$API_URL/health" 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "ERROR: Health check failed"
    if [ -n "$ALERT_WEBHOOK" ]; then
        curl -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d '{"text":"🚨 Genio health check failed!"}'
    fi
    exit 1
fi

echo "✓ Health check passed"
echo "$HEALTH" | jq .

# Check metrics endpoint
METRICS=$(curl -sf "$API_URL/metrics" 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "WARNING: Metrics endpoint not responding"
    exit 1
fi

echo "✓ Metrics endpoint responding"

# Parse SLIs
echo ""
echo "SLI Status:"
echo "$METRICS" | jq -r '.slis | to_entries[] | "  \(.key): \(.value.status) (current: \(.value.current), target: \(.value.target))"'

# Check for degraded SLIs
DEGRADED=$(echo "$METRICS" | jq -r '.slis | to_entries[] | select(.value.status == "alert") | .key')
if [ -n "$DEGRADED" ]; then
    echo ""
    echo "WARNING: Degraded SLIs detected:"
    echo "$DEGRADED"
    exit 1
fi

echo ""
echo "✓ All systems healthy"
