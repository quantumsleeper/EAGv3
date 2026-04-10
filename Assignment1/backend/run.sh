#!/bin/bash
cd "$(dirname "$0")"

if [ -f "/usr/local/Cellar/python@3.11/3.11.10/bin/python3.11" ]; then
  PYTHON_BIN="/usr/local/Cellar/python@3.11/3.11.10/bin/python3.11"
else
  PYTHON_BIN="python3"
fi

if [ ! -d "venv" ]; then
  echo "Creating virtual environment using $PYTHON_BIN..."
  $PYTHON_BIN -m venv venv
fi

source venv/bin/activate
echo "Installing dependencies (this might take a while for large ML models)..."
# Using a high timeout because PyTorch is a massive ~1.5GB+ download which often times out!
if ! pip install --default-timeout=1000 -r requirements.txt; then
  echo ""
  echo "❌ Error: Pip failed to download dependencies (likely a network timeout or connection drop). Please try again."
  exit 1
fi

echo "Dependencies installed."
echo "✅ Starting Karaoke Backend Server! 🎤"
uvicorn main:app --host 0.0.0.0 --port 8000
