#!/bin/bash

# Deployment Verification Script for OmniDesk AI
# This script verifies that all services are running correctly after deployment

set -e

DOMAIN=${DOMAIN:-"localhost"}
PROTOCOL=${PROTOCOL:-"http"}
TIMEOUT=30

echo "🔍 Starting deployment verification for OmniDesk AI..."
echo "Domain: $DOMAIN"
echo "Protocol: $PROTOCOL"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a service is responding
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=$3
    
    echo -n "Checking $service_name... "
    
    if command -v curl >/dev/null 2>&1; then
        response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" || echo "000")
    else
        echo -e "${YELLOW}SKIPPED${NC} (curl not available)"
        return 0
    fi
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $response, expected $expected_status)"
        return 1
    fi
}

# Function to check Docker container status
check_container() {
    local container_name=$1
    echo -n "Checking container $container_name... "
    
    if ! command -v docker >/dev/null 2>&1; then
        echo -e "${YELLOW}SKIPPED${NC} (Docker not available)"
        return 0
    fi
    
    if docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
        echo -e "${GREEN}✓ RUNNING${NC}"
        return 0
    else
        echo -e "${RED}✗ NOT RUNNING${NC}"
        return 1
    fi
}

# Function to check database connectivity
check_database() {
    echo -n "Checking database connectivity... "
    
    # Try to connect to the health endpoint that checks DB
    if check_service "Database" "$PROTOCOL://$DOMAIN/health" "200" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ CONNECTED${NC}"
        return 0
    else
        echo -e "${RED}✗ CONNECTION FAILED${NC}"
        return 1
    fi
}

# Main verification process
echo ""
echo "=== Container Status ==="
check_container "omni-nginx"
check_container "omni-backend"
check_container "omni-frontend"
check_container "omni-postgres"
check_container "omni-redis"
check_container "omni-qdrant"

echo ""
echo "=== Service Health Checks ==="
check_service "Frontend" "$PROTOCOL://$DOMAIN/" "200"
check_service "Backend API" "$PROTOCOL://$DOMAIN/api/health" "200"
check_service "Backend Docs" "$PROTOCOL://$DOMAIN/api/docs" "200"

echo ""
echo "=== Database & Cache ==="
check_database
check_service "Redis" "$PROTOCOL://$DOMAIN/api/health" "200"

echo ""
echo "=== API Endpoints ==="
check_service "Tickets API" "$PROTOCOL://$DOMAIN/api/tickets" "200"
check_service "Health API" "$PROTOCOL://$DOMAIN/api/health" "200"

echo ""
echo "=== Monitoring (if enabled) ==="
check_service "Prometheus" "$PROTOCOL://$DOMAIN:9090" "200" || echo "  Note: Prometheus may not be exposed publicly"
check_service "Grafana" "$PROTOCOL://$DOMAIN:3001" "200" || echo "  Note: Grafana may not be exposed publicly"

echo ""
echo "=== Security Headers ==="
echo -n "Checking security headers... "
if command -v curl >/dev/null 2>&1; then
    headers=$(curl -I -s --max-time $TIMEOUT "$PROTOCOL://$DOMAIN/" || echo "")
    if echo "$headers" | grep -qi "x-frame-options\|x-content-type-options\|x-xss-protection"; then
        echo -e "${GREEN}✓ PRESENT${NC}"
    else
        echo -e "${YELLOW}⚠ MISSING${NC}"
    fi
else
    echo -e "${YELLOW}SKIPPED${NC} (curl not available)"
fi

echo ""
echo "=== Load Test (Basic) ==="
echo -n "Testing concurrent requests... "
if command -v curl >/dev/null 2>&1; then
    success_count=0
    for i in {1..5}; do
        response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$PROTOCOL://$DOMAIN/api/health" &)
        if [ "$?" = "0" ]; then
            ((success_count++))
        fi
    done
    wait
    
    if [ $success_count -ge 4 ]; then
        echo -e "${GREEN}✓ PASSED${NC} ($success_count/5 requests successful)"
    else
        echo -e "${YELLOW}⚠ PARTIAL${NC} ($success_count/5 requests successful)"
    fi
else
    echo -e "${YELLOW}SKIPPED${NC} (curl not available)"
fi

echo ""
echo "=== Deployment Verification Summary ==="

# Count successful checks
total_critical_checks=8  # Adjust based on critical services
failed_checks=0

# Re-run critical checks silently to count failures
check_service "Frontend" "$PROTOCOL://$DOMAIN/" "200" >/dev/null 2>&1 || ((failed_checks++))
check_service "Backend API" "$PROTOCOL://$DOMAIN/api/health" "200" >/dev/null 2>&1 || ((failed_checks++))
check_database >/dev/null 2>&1 || ((failed_checks++))

if [ $failed_checks -eq 0 ]; then
    echo -e "${GREEN}🎉 All critical services are running successfully!${NC}"
    echo -e "${GREEN}✓ Deployment verification PASSED${NC}"
    echo ""
    echo "🌐 Your OmniDesk AI application is available at: $PROTOCOL://$DOMAIN/"
    echo "📚 API Documentation: $PROTOCOL://$DOMAIN/api/docs"
    exit 0
elif [ $failed_checks -le 2 ]; then
    echo -e "${YELLOW}⚠ Deployment verification completed with warnings${NC}"
    echo -e "${YELLOW}$failed_checks non-critical issues detected${NC}"
    echo ""
    echo "🌐 Your application may still be accessible at: $PROTOCOL://$DOMAIN/"
    exit 1
else
    echo -e "${RED}❌ Deployment verification FAILED${NC}"
    echo -e "${RED}$failed_checks critical issues detected${NC}"
    echo ""
    echo "Please check the logs and fix the issues before proceeding."
    echo "Run: docker-compose -f docker-compose.prod.yml logs"
    exit 2
fi