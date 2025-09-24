#!/bin/bash
# Monitor memory usage and alert if high

echo "📊 Starting BodyScript memory monitor..."
echo "Press Ctrl+C to stop monitoring"
echo ""

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

while true; do
    # Get container name (might be bodyscript-bodyscript-1 or bodyscript_bodyscript_1)
    CONTAINER_NAME=$(docker ps --format "{{.Names}}" | grep bodyscript | head -1)

    if [ -z "$CONTAINER_NAME" ]; then
        echo -e "${RED}❌ No BodyScript container running${NC}"
        sleep 5
        continue
    fi

    # Get memory usage percentage
    MEMORY_PERCENT=$(docker stats --no-stream --format "{{.MemPerc}}" $CONTAINER_NAME | sed 's/%//')

    # Get memory usage in MB
    MEMORY_USAGE=$(docker stats --no-stream --format "{{.MemUsage}}" $CONTAINER_NAME)

    # Get current timestamp
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # Determine status based on memory percentage
    if (( $(echo "$MEMORY_PERCENT > 80" | bc -l) )); then
        echo -e "${RED}⚠️  [$TIMESTAMP] WARNING: High memory usage!${NC}"
        echo -e "${RED}   Memory: ${MEMORY_USAGE} (${MEMORY_PERCENT}%)${NC}"
        echo -e "${YELLOW}   Consider switching to native installation${NC}"

        # Optional: Send alert (uncomment if you have mail configured)
        # echo "High memory alert: ${MEMORY_PERCENT}%" | mail -s "BodyScript Memory Alert" your@email.com

    elif (( $(echo "$MEMORY_PERCENT > 60" | bc -l) )); then
        echo -e "${YELLOW}⚡ [$TIMESTAMP] Memory usage moderate${NC}"
        echo -e "   Memory: ${MEMORY_USAGE} (${MEMORY_PERCENT}%)"

    else
        echo -e "${GREEN}✅ [$TIMESTAMP] Memory OK${NC}"
        echo -e "   Memory: ${MEMORY_USAGE} (${MEMORY_PERCENT}%)"
    fi

    # Also show system memory
    if command -v free &> /dev/null; then
        SYSTEM_MEM=$(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
        echo -e "   System: ${SYSTEM_MEM} used"
    fi

    echo ""
    sleep 60
done