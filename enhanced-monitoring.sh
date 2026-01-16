#!/bin/bash

# Enhanced SBS Integration Monitoring Script
# Provides real-time health checks and performance metrics

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SBS Integration - Enhanced Monitoring${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Function to check service health
check_service_health() {
    local service_name=$1
    local port=$2
    local url="http://localhost:${port}/health"
    
    echo -n "Checking ${service_name} (${port}): "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "${url}" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ Healthy${NC}"
        
        # Get detailed response
        details=$(curl -s "${url}" 2>/dev/null)
        echo "  Response: ${details}"
        
        # Measure response time
        response_time=$(curl -s -o /dev/null -w "%{time_total}" "${url}" 2>/dev/null)
        echo -e "  Response time: ${response_time}s"
        
        return 0
    elif [ "$response" = "000" ]; then
        echo -e "${RED}✗ Unreachable${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠ HTTP ${response}${NC}"
        return 1
    fi
}

# Function to check Docker container status
check_docker_status() {
    echo -e "\n${BLUE}Docker Container Status:${NC}"
    docker ps --filter "name=sbs-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No containers found"
}

# Function to check database connectivity
check_database() {
    echo -e "\n${BLUE}Database Status:${NC}"
    
    db_status=$(docker exec -i sbs-postgres pg_isready -U postgres 2>/dev/null || echo "error")
    
    if [[ $db_status == *"accepting connections"* ]]; then
        echo -e "${GREEN}✓ PostgreSQL accepting connections${NC}"
        
        # Get table count
        table_count=$(docker exec -i sbs-postgres psql -U postgres -d sbs_integration -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")
        echo "  Tables: ${table_count}"
        
        # Get record counts
        echo -e "\n  ${BLUE}Sample Data:${NC}"
        sbs_codes=$(docker exec -i sbs-postgres psql -U postgres -d sbs_integration -t -c "SELECT COUNT(*) FROM sbs_master_catalogue;" 2>/dev/null || echo "0")
        facilities=$(docker exec -i sbs-postgres psql -U postgres -d sbs_integration -t -c "SELECT COUNT(*) FROM facilities;" 2>/dev/null || echo "0")
        
        echo "    SBS Codes: ${sbs_codes}"
        echo "    Facilities: ${facilities}"
    else
        echo -e "${RED}✗ PostgreSQL not accessible${NC}"
    fi
}

# Function to test end-to-end workflow
test_normalization() {
    echo -e "\n${BLUE}Testing Code Normalization:${NC}"
    
    response=$(curl -s -X POST http://localhost:8000/normalize \
        -H 'Content-Type: application/json' \
        -d '{
            "facility_id": 1,
            "internal_code": "LAB-CBC-01",
            "description": "Complete Blood Count Test"
        }' 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Normalization working${NC}"
        echo "  Response: ${response}" | head -c 200
        echo "..."
    else
        echo -e "${RED}✗ Normalization failed${NC}"
    fi
}

# Function to check n8n webhook
check_n8n_webhook() {
    echo -e "\n${BLUE}n8n Webhook Status:${NC}"
    
    # Check if n8n is accessible locally
    n8n_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5678" 2>/dev/null || echo "000")
    
    if [ "$n8n_status" = "200" ] || [ "$n8n_status" = "401" ]; then
        echo -e "${GREEN}✓ n8n accessible${NC}"
    else
        echo -e "${YELLOW}⚠ n8n not accessible locally (might be remote)${NC}"
    fi
}

# Function to display resource usage
check_resources() {
    echo -e "\n${BLUE}Resource Usage:${NC}"
    
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
        $(docker ps --filter "name=sbs-" -q) 2>/dev/null || echo "No stats available"
}

# Main monitoring sequence
echo -e "${BLUE}Service Health Checks:${NC}\n"

check_service_health "Normalizer" "8000"
echo ""
check_service_health "Signer" "8001"
echo ""
check_service_health "Financial Rules" "8002"
echo ""
check_service_health "NPHIES Bridge" "8003"

check_docker_status
check_database
test_normalization
check_n8n_webhook
check_resources

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}Monitoring Complete${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Performance summary
echo -e "${BLUE}Quick Summary:${NC}"
echo "Run this script regularly to monitor system health"
echo "For continuous monitoring: watch -n 10 ./enhanced-monitoring.sh"
echo ""
