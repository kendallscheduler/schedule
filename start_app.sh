#!/bin/bash

# Kill any existing processes on ports 3000 and 8000
echo "Stopping any existing scheduling servers..."
lsof -ti :8000 | xargs kill -9 2>/dev/null
lsof -ti :3000 | xargs kill -9 2>/dev/null

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start Backend
echo "Starting Backend Server..."
cd "$DIR/webapp/backend"
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi
# Run in background
nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend running on http://127.0.0.1:8000 (PID: $BACKEND_PID)"

# Start Frontend
echo "Starting Frontend Server..."
cd "$DIR/webapp/frontend"
if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies (this may take a minute)..."
    npm install
fi
# Run in background
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend running on http://localhost:3000 (PID: $FRONTEND_PID)"

echo ""
echo "🎉 Kendall Scheduler is running!"
echo "👉 Open your browser to: http://localhost:3000"
echo ""
echo "To stop the servers, run: lsof -ti :3000 :8000 | xargs kill -9"
