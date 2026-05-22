#!/bin/bash
# Start FastAPI backend server in the background on port 8000
echo "🚀 Starting FastAPI backend on port 8000..."
uvicorn main:app --host 127.0.0.1 --port 8000 &

# Start Streamlit frontend on the public port injected by the host platform
echo "📊 Starting Streamlit frontend on port $PORT..."
streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0
