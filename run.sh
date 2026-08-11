#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/backend"
python -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -r requirements.txt -q
echo "[test] running unit tests..."
pytest -q
echo "[serve] starting engine on http://localhost:8000"
uvicorn app.main:app --reload --port 8000