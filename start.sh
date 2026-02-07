#!/bin/bash
# Start Mission Control Dashboard

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Start the app
echo "🦊 Starting Mission Control Dashboard..."
echo "   URL: http://localhost:8080"
echo "   Press Ctrl+C to stop"
echo ""

python app.py
