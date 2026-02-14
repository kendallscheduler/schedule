#!/bin/bash
# Run backend and frontend for IM Residency Schedule Generator
cd "$(dirname "$0")"

echo "Starting backend on http://localhost:8000..."
cd backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cd ..

echo "Starting frontend on http://localhost:3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Backend: http://localhost:8000 (docs: http://localhost:8000/docs)"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both."
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
