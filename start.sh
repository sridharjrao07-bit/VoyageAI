#!/usr/bin/env bash
set -e

cd backend
pip install --no-cache-dir -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
