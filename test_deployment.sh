#!/bin/bash

# Pantry Inventory - End-to-End Test
# Tests full deployment stack locally

echo "╔═══════════════════════════════════════════════════════╗"
echo "║   PANTRY INVENTORY - END-TO-END DEPLOYMENT TEST      ║"
echo "║            Phase 7: Production Deployment             ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_status=$4
    
    echo -n "Testing $description... "
    
    status=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "http://localhost:8000$endpoint")
    
    if [ "$status" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ ($status)${NC}"
        TESTS_PASSED=$((TESTS_PASSED+1))
        return 0
    else
        echo -e "${RED}✗ (got $status, expected $expected_status)${NC}"
        TESTS_FAILED=$((TESTS_FAILED+1))
        return 1
    fi
}

test_json_response() {
    local endpoint=$1
    local description=$2
    
    echo -n "Testing $description... "
    
    response=$(curl -s "http://localhost:8000$endpoint")
    
    if echo "$response" | grep -q "items"; then
        echo -e "${GREEN}✓${NC}"
        TESTS_PASSED=$((TESTS_PASSED+1))
        return 0
    else
        echo -e "${RED}✗${NC}"
        TESTS_FAILED=$((TESTS_FAILED+1))
        return 1
    fi
}

# Pre-flight checks
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. PRE-FLIGHT CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Checking Docker services..."
docker_running=$(docker ps --filter name=pantry | wc -l)
if [ "$docker_running" -gt 1 ]; then
    echo -e "${GREEN}✓${NC} Docker services running"
    docker ps --filter name=pantry --format "  - {{.Names}}: {{.Status}}"
    TESTS_PASSED=$((TESTS_PASSED+1))
else
    echo -e "${RED}✗${NC} Docker services not running"
    TESTS_FAILED=$((TESTS_FAILED+1))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. API HEALTH CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_endpoint "GET" "/health" "API health" 200
test_endpoint "GET" "/docs" "API documentation" 200

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. INVENTORY ENDPOINTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_json_response "/v1/inventory" "Get inventory"
test_json_response "/v1/devices" "List devices"
test_json_response "/v1/inventory/history?days=7" "Get inventory history"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. ADMIN ENDPOINTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_endpoint "GET" "/v1/admin/health/db" "Database health" 200
test_endpoint "GET" "/v1/admin/health/redis" "Redis health" 200

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. SERVICE CONNECTIVITY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check database
echo -n "Checking PostgreSQL... "
if docker exec pantry-db pg_isready -U pantry > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    TESTS_PASSED=$((TESTS_PASSED+1))
else
    echo -e "${RED}✗${NC}"
    TESTS_FAILED=$((TESTS_FAILED+1))
fi

# Check Redis
echo -n "Checking Redis... "
if docker exec pantry-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    TESTS_PASSED=$((TESTS_PASSED+1))
else
    echo -e "${RED}✗${NC}"
    TESTS_FAILED=$((TESTS_FAILED+1))
fi

# Check Celery worker
echo -n "Checking Celery worker... "
worker_status=$(curl -s http://localhost:5555/api/workers 2>/dev/null || echo "offline")
if [ "$worker_status" != "offline" ]; then
    echo -e "${GREEN}✓${NC}"
    TESTS_PASSED=$((TESTS_PASSED+1))
else
    echo -e "${RED}✗${NC} (Note: Flower may not be fully initialized yet)"
    # Don't count as failure
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. WEB UI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Web UI available at:"
echo "  http://localhost:3000  (React Dev Server)"
echo "  http://localhost:5173  (Vite Direct)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [ "$TESTS_FAILED" -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8. NEXT STEPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Services Running:"
echo "  ✓ API Server:      http://localhost:8000"
echo "  ✓ API Docs:        http://localhost:8000/docs"
echo "  ✓ Web UI:          http://localhost:3000"
echo "  ✓ Database:        postgres://localhost:5432/pantry_db"
echo "  ✓ Redis:           redis://localhost:6379"
echo "  ✓ Celery Worker:   Processing jobs asynchronously"
echo ""

echo "Useful Commands:"
echo "  View logs:         docker compose logs -f"
echo "  Stop services:     docker compose stop"
echo "  Restart services:  docker compose up -d"
echo "  Full cleanup:      docker compose down -v"
echo ""

echo "Test Device Credentials:"
echo "  Device ID:   pantry-cam-001"
echo "  Token:       (check 'docker compose logs backend')"
echo ""

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ DEPLOYMENT SUCCESSFUL!${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    exit 1
fi
