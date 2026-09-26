#!/usr/bin/env bash
# Lanceur en ligne de commande pour Super Video
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    "$DIR/.venv/bin/pip" install -r requirements.txt
fi

if [ ! -f ".env" ]; then
    cp .env.example .env
fi

(
    sleep 2
    open "http://127.0.0.1:7860" || xdg-open "http://127.0.0.1:7860"
) &

"$DIR/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 7860
