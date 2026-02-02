#!/bin/bash
# Simple test setup and execution script for Docker-based testing

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🔧 rsync-tailscale-docker Test Setup${NC}"
echo "========================================"

# Check Docker availability
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed${NC}"
    exit 1
fi

# Check if docker-compose is available (either standalone or plugin)
COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}❌ Error: Docker Compose is not available${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are available${NC}"

# Create test logs directory
mkdir -p test-logs
echo -e "${GREEN}✓ Created test-logs directory${NC}"

# Build the test image
echo -e "${BLUE}🐳 Building test Docker image...${NC}"
$COMPOSE_CMD build rsync-backup-test
echo -e "${GREEN}✓ Test image built successfully${NC}"

echo ""
echo -e "${BLUE}🧪 Available Test Commands:${NC}"
echo "  ./run_tests.sh docker-all      # Run all tests"
echo "  ./run_tests.sh docker-unit     # Run unit tests only"
echo "  ./run_tests.sh docker-coverage # Run with coverage report"
echo "  ./run_tests.sh docker-shell    # Interactive container shell"
echo ""

# Run a quick test to verify everything works
echo -e "${BLUE}🔍 Running quick verification test...${NC}"
if $COMPOSE_CMD run --rm rsync-backup-test /run_tests.sh help &> /dev/null; then
    echo -e "${GREEN}✓ Test environment is ready!${NC}"
    echo ""
    echo -e "${BLUE}Quick Start:${NC}"
    echo "  ./run_tests.sh docker-all"
    echo ""
else
    echo -e "${RED}❌ Test environment setup failed${NC}"
    exit 1
fi