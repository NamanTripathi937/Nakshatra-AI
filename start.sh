#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Nakshatra AI...${NC}\n"

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${RED}Shutting down services...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start Backend
echo -e "${BLUE}📡 Starting Backend (FastAPI)...${NC}"
cd backend
source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start Frontend
echo -e "${BLUE}🌐 Starting Frontend (Next.js)...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "\n${GREEN}✅ Services started successfully!${NC}"
echo -e "${BLUE}Backend:${NC}  http://localhost:8000"
echo -e "${BLUE}Frontend:${NC} http://localhost:3000"
echo -e "\n${RED}Press Ctrl+C to stop all services${NC}\n"

# Wait for all background processes
wait
