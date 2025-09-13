#!/bin/bash

# TalkingPhoto AI MVP - Quick Start Script
# Epic 4: User Experience & Interface

echo "🎬 Starting TalkingPhoto AI MVP - Streamlit Frontend"
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "main_app.py" ]; then
    echo "❌ Please run this script from the talkingphoto-mvp directory"
    exit 1
fi

# Set environment variables
export STREAMLIT_ENV=${STREAMLIT_ENV:-development}
export STREAMLIT_PORT=${STREAMLIT_PORT:-8501}
export STREAMLIT_HOST=${STREAMLIT_HOST:-0.0.0.0}

echo "📦 Checking dependencies..."

# Check if streamlit is installed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "⚠️ Streamlit not found. Installing dependencies..."
    pip3 install -r requirements-streamlit.txt
fi

# Check backend connection (optional)
echo "🔗 Checking backend connection..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:5000"
    BACKEND_AVAILABLE=true
else
    echo "⚠️ Backend not available. Frontend will run in demo mode."
    BACKEND_AVAILABLE=false
fi

echo "🚀 Starting Streamlit application..."
echo "Environment: $STREAMLIT_ENV"
echo "Port: $STREAMLIT_PORT"
echo "Host: $STREAMLIT_HOST"
echo ""

# Choose startup method based on environment
if [ "$STREAMLIT_ENV" = "production" ]; then
    echo "📊 Starting in production mode..."
    python3 run_streamlit.py --env production --port $STREAMLIT_PORT --host $STREAMLIT_HOST
else
    echo "🛠️ Starting in development mode..."
    
    # Use streamlit directly for development
    streamlit run main_app.py \
        --server.port $STREAMLIT_PORT \
        --server.address $STREAMLIT_HOST \
        --logger.level info \
        --server.headless false
fi