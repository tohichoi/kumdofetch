#!/usr/bin/env bash
# Physical constraints check: file/function length limits (code-quality.md §2)
# and secret/PII leak scan (§6). Run before committing.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAX_LINES=300
MAX_FUNCTION_LINES=50
status=0

echo "[1/4] Python file length (max ${MAX_LINES} lines)"
while IFS= read -r -d '' file; do
    lines=$(wc -l <"$file")
    if [ "$lines" -gt "$MAX_LINES" ]; then
        echo "  VIOLATION: $file has $lines lines"
        status=1
    fi
done < <(find "$ROOT/app" "$ROOT/config" "$ROOT/scripts" "$ROOT/tests" -name '*.py' -print0)

echo "[2/4] Shell file length (max ${MAX_LINES} lines)"
while IFS= read -r -d '' file; do
    lines=$(wc -l <"$file")
    if [ "$lines" -gt "$MAX_LINES" ]; then
        echo "  VIOLATION: $file has $lines lines"
        status=1
    fi
done < <(find "$ROOT/scripts" -name '*.sh' -print0)

echo "[3/4] Python function length (max ${MAX_FUNCTION_LINES} lines)"
if ! uv run python - "$ROOT" "$MAX_FUNCTION_LINES" <<'PY'
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
limit = int(sys.argv[2])
failures = []
for name in ("app", "config", "scripts", "tests"):
    for path in (root / name).rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                if length > limit:
                    failures.append(f"  VIOLATION: {path}:{node.lineno} {node.name} has {length} lines")
if failures:
    print("\n".join(failures))
    sys.exit(1)
PY
then
    status=1
fi

echo "[4/4] Secret / PII pattern scan"
pattern='(AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9]{20,}|[0-9]{6}-[0-9]{7}|01[0-9]-[0-9]{3,4}-[0-9]{4})'
if matches=$(grep -rInE "$pattern" "$ROOT" \
    --include='*.py' --include='*.md' --include='*.sh' --include='*.toml' \
    --include='*.yaml' --include='*.yml' \
    --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv --exclude-dir=.serena \
    --exclude-dir=.ruff_cache --exclude-dir=.pytest_cache --exclude-dir=__pycache__ \
    2>/dev/null); then
    echo "  VIOLATION: possible secret/PII found"
    echo "$matches"
    status=1
fi

if [ "$status" -eq 0 ]; then
    echo "OK: all physical constraints satisfied"
fi
exit "$status"
