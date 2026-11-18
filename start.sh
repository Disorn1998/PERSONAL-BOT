#!/usr/bin/env bash
# persona-bot — Unix quick start (DoD 1 companion for Linux)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — add GROQ_API_KEY and GROQ_MODEL_* then re-run if needed."
fi

mkdir -p data
uv sync
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
# persona-bot CLI binds 127.0.0.1; see docs/FIRST_RUN.md for Streamlit email skip.
exec uv run persona-bot
