#!/usr/bin/env bash
# Starts backend (8000) and frontend (5173). Ctrl+C stops both.
cd "$(dirname "$0")"; ROOT=$PWD
trap 'kill 0' EXIT
( cd "$ROOT/backend" && source .venv/bin/activate && python manage.py runserver 8000 ) &
( cd "$ROOT/frontend" && npm run dev ) &
sleep 4; open http://localhost:5173 2>/dev/null || true
wait
