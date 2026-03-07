#!/usr/bin/env bash
# Helper script to launch the orchestration service in development mode.
# Usage: ./run.sh [--mistral | --openrouter]

set -euo pipefail

if [[ "$1" == "--mistral" ]]; then
    echo "Using Mistral API for model calls"
    export MISTRAL_API_KEY="${MISTRAL_API_KEY:-}"
elif [[ "$1" == "--openrouter" ]]; then
    echo "Using OpenRouter API for model calls"
    export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
else
    echo "No provider override; will use whichever key is defined in .env"
fi

# load .env if exists
if [[ -f .env ]]; then
    # shellcheck disable=SC1091
    source .env
fi

uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
