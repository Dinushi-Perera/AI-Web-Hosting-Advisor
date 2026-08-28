#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON="$PROJECT_ROOT/backend/venv/bin/python"
if [ ! -x "$PYTHON" ]; then PYTHON=python; fi

mkdir -p "$PROJECT_ROOT/backend/test-results" "$PROJECT_ROOT/frontend/test-results"

cd "$PROJECT_ROOT/backend"
"$PYTHON" -m pytest --junitxml=test-results/junit.xml

cd "$PROJECT_ROOT/frontend"
npm run ci
