#!/usr/bin/env bash
# Check loop + hook health for a project.
set -euo pipefail

TARGET="${1:-.}"
TARGET="$(cd "$TARGET" && pwd)"

echo "cursor-loop doctor — ${TARGET}"
echo

if [[ ! -f "${TARGET}/.cursor/cursor-loop.json" ]]; then
  echo "FAIL manifest missing (.cursor/cursor-loop.json)"
  exit 1
fi
echo "OK   manifest present"

python3 -c "
import json
from pathlib import Path
root = Path('${TARGET}')
manifest = json.loads((root / '.cursor/cursor-loop.json').read_text())
pkg = root / manifest['package_root']
for rel in ['scripts/loop_hook_lib.py', 'scripts/agent-loop.sh', 'scripts/hook_bind.py']:
    path = pkg / rel
    print(('OK  ' if path.is_file() else 'FAIL') + ' ' + str(path))
"

for hook in loop-bind.sh loop-survival.sh _common.sh; do
  path="${TARGET}/.cursor/hooks/${hook}"
  if [[ -x "$path" || -L "$path" ]]; then
    echo "OK   ${path}"
  else
    echo "FAIL ${path}"
  fi
done

echo
bash "${TARGET}/$(python3 -c "import json; from pathlib import Path; m=json.loads(Path('${TARGET}/.cursor/cursor-loop.json').read_text()); print(m['package_root']+'/scripts/loop-status.sh')")" 2>/dev/null || true
