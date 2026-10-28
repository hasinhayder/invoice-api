#!/usr/bin/env bash
# Start the Invoice Builder API on port 8120 (override with PORT=... ./start.sh).
set -euo pipefail
cd "$(dirname "$0")"
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8120}"
exec uv run invoice-api
