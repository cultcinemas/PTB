#!/bin/bash

# PTB Telegram Bot - VPS Deployment Script
# This script handles deployment on a VPS server

set -e

echo "🚀 Starting PTB Telegram Bot deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not available. Please install Docker Compose.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your actual configuration before continuing.${NC}"
    echo -e "${YELLOW}   Run: nano .env${NC}"
    exit 1
fi

# Validate critical environment variables
echo "🔍 Validating configuration..."
source .env

if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" = "your_bot_token_here" ]; then
    echo -e "${RED}❌ BOT_TOKEN not configured in .env file${NC}"
    exit 1
fi

if [ -z "$MONGODB_URI" ] || [[ "$MONGODB_URI" == *"your_mongodb_connection_string"* ]]; then
    echo -e "${RED}❌ MONGODB_URI not configured in .env file${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration validated${NC}"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# Build and start the application
echo "🏗️  Building and starting containers..."
docker-compose -f docker-compose.prod.yml up --build -d

# Check if container is running
sleep 10
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo -e "${GREEN}✅ PTB Bot deployed successfully!${NC}"
    echo -e "${GREEN}✅ Bot is running in detached mode${NC}"
    
    # Show container logs
    echo -e "${YELLOW}📋 Recent logs:${NC}"
    docker-compose -f docker-compose.prod.yml logs --tail=20
    
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo -e "${YELLOW}💡 To view logs: docker-compose -f docker-compose.prod.yml logs -f${NC}"
    echo -e "${YELLOW}💡 To stop: docker-compose -f docker-compose.prod.yml down${NC}"
    echo -e "${YELLOW}💡 To restart: docker-compose -f docker-compose.prod.yml restart${NC}"
else
    echo -e "${RED}❌ Deployment failed. Container is not running.${NC}"
    echo -e "${RED}📋 Error logs:${NC}"
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi
