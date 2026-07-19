#!/usr/bin/env bash

set -e

# ==========================
# Colors
# ==========================
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting Nakshatra AI...${NC}\n"

# ==========================
# Ensure we're in project root
# ==========================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ==========================
# Cleanup
# ==========================
cleanup() {
    echo -e "\n${RED}Stopping services...${NC}"

    if [[ -n "$BACKEND_PID" ]]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi

    if [[ -n "$FRONTEND_PID" ]]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi

    wait 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# ==========================
# Locate Python in backend venv
# ==========================
if [[ -f "backend/venv/Scripts/python.exe" ]]; then
    PYTHON="backend/venv/Scripts/python.exe"
elif [[ -f "backend/venv/bin/python" ]]; then
    PYTHON="backend/venv/bin/python"
else
    echo -e "${RED}❌ Virtual environment not found.${NC}"
    echo "Expected one of:"
    echo "  backend/venv/Scripts/python.exe"
    echo "  backend/venv/bin/python"
    exit 1
fi

# ==========================
# Verify FastAPI exists
# ==========================
if ! "$PYTHON" -m pip show fastapi >/dev/null 2>&1; then
    echo -e "${RED}❌ FastAPI is not installed in backend/venv${NC}"
    echo "Run:"
    echo "cd backend"
    echo "pip install -r requirements.txt"
    exit 1
fi

# ==========================
# Verify frontend dependencies
# ==========================
if [[ ! -d "frontend/node_modules" ]]; then
    echo -e "${RED}❌ frontend/node_modules not found.${NC}"
    echo "Run:"
    echo "cd frontend"
    echo "npm install"
    exit 1
fi

# ==========================
# Start Backend
# ==========================
echo -e "${BLUE}📡 Starting Backend (FastAPI)...${NC}"

(
    cd backend
    exec ../"$PYTHON" -m uvicorn main:app \
        --reload \
        --host 0.0.0.0 \
        --port 8000
) &

BACKEND_PID=$!

sleep 2

# ==========================
# Start Frontend
# ==========================
echo -e "${BLUE}🌐 Starting Frontend (Next.js)...${NC}"

(
    cd frontend
    exec npm run dev
) &

FRONTEND_PID=$!

echo
echo -e "${GREEN}✅ Services started!${NC}"
echo -e "${BLUE}Backend :${NC} http://localhost:8000"
echo -e "${BLUE}Frontend:${NC} http://localhost:3000"
echo
echo -e "${YELLOW}Press Ctrl+C to stop both services.${NC}"
echo

wait "$BACKEND_PID" "$FRONTEND_PID"