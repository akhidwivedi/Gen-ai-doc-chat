#!/usr/bin/env bash
# Read-only: reports what is installed. Changes nothing.
ok(){ echo "  [ok]   $1"; }; no(){ echo "  [MISS] $1"; }
echo "== Tools"
command -v brew >/dev/null && ok "Homebrew $(brew --version | head -1)" || no "Homebrew (https://brew.sh)"
PY=$(command -v python3.12 || command -v python3.11 || command -v python3.13 || command -v python3)
if [ -n "$PY" ] && "$PY" -c 'import sys; sys.exit(0 if sys.version_info>=(3,11) else 1)'; then ok "Python $($PY --version) ($PY)"; else no "Python 3.11+  ->  brew install python@3.12"; fi
if command -v node >/dev/null && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 20 ]; then ok "Node $(node --version)"; else no "Node 20+  ->  brew install node"; fi
echo "== PostgreSQL (optional; SQLite works without it)"
if command -v psql >/dev/null; then ok "psql $(psql --version)"; pg_isready >/dev/null 2>&1 && ok "server running" || no "server not running  ->  brew services start postgresql@16"; else no "PostgreSQL  ->  brew install postgresql@16"; fi
echo "== Ports"
for p in 8000 5173; do lsof -i :$p >/dev/null 2>&1 && no "port $p is in use" || ok "port $p free"; done
echo "== API key"
grep -Eq '^GEMINI_API_KEY=.+' "$(dirname "$0")/backend/.env" 2>/dev/null && ok "GEMINI_API_KEY set" || no "GEMINI_API_KEY empty in backend/.env (needed for chat answers)"
