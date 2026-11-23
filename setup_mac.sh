#!/usr/bin/env bash
# One-time setup. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")"
ROOT=$PWD
PY=$(command -v python3.12 || command -v python3.11 || command -v python3.13 || true)
[ -n "$PY" ] || { echo "Need Python 3.11+: brew install python@3.12"; exit 1; }
command -v node >/dev/null || { echo "Need Node: brew install node"; exit 1; }

echo "==> Backend"
cd "$ROOT/backend"
[ -f .env ] || cp .env.example .env
if command -v psql >/dev/null && pg_isready >/dev/null 2>&1; then
  echo "    PostgreSQL detected -> using it"
  createdb docchat 2>/dev/null || true
  sed -i '' -e 's/^DB_ENGINE=.*/DB_ENGINE=postgres/' -e "s/^DB_USER=.*/DB_USER=$(whoami)/" -e 's/^DB_PASSWORD=.*/DB_PASSWORD=/' .env
else
  echo "    PostgreSQL not running -> using SQLite for now (see backend/README.md to switch)"
  sed -i '' 's/^DB_ENGINE=.*/DB_ENGINE=sqlite/' .env
fi
[ -d .venv ] || "$PY" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt
python manage.py migrate
python manage.py warmup_models

echo "==> Frontend"
cd "$ROOT/frontend"
[ -f .env ] || cp .env.example .env
npm install

echo
echo "Setup done. Add your key:  open -e $ROOT/backend/.env   (GEMINI_API_KEY=...)"
echo "Then run:  $ROOT/run_mac.sh"
