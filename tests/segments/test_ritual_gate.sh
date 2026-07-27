#!/usr/bin/env bash
# Segment: ritual_phase + validate_ritual_gate
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPTS="${ROOT}/scripts"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

export PYTHONPATH="${SCRIPTS}:${PYTHONPATH:-}"

python3 - <<'PY'
import ritual_phase as rp

assert rp.validate_transition("1-wake", "2-orient") == (True, "")
ok, msg = rp.validate_transition("4-execute", "9-arm")
assert not ok and "skip" in msg
assert rp.allowed_phase_on_wake("9-arm") == "1-wake"
print("OK ritual_phase transitions")
PY

STATE="${TMP}/STATE.md"
cat > "$STATE" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `4-execute` |
| review_status | pending |
| code_changed | no |
EOF

if python3 "${SCRIPTS}/validate_ritual_gate.py" \
  --project "$TMP" --loop-id worker-relay --state-file STATE.md --mode arm 2>/dev/null; then
  echo "FAIL: gate should reject phase 4 before arm"
  exit 1
fi
echo "OK gate rejects early phase"

cat > "$STATE" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `8-close` |
| review_status | skipped |
| review_skip_reason | docs only |
| code_changed | no |
EOF

python3 "${SCRIPTS}/validate_ritual_gate.py" \
  --project "$TMP" --loop-id worker-relay --state-file STATE.md --mode arm
echo "OK gate accepts 8-close skipped review"

cat > "$STATE" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `8-close` |
| review_status | skipped |
| review_skip_reason | docs only |
| code_changed | no |
| worktree_status | active |
EOF

if python3 "${SCRIPTS}/validate_ritual_gate.py" \
  --project "$TMP" --loop-id worker-relay --state-file STATE.md --mode arm 2>/dev/null; then
  echo "FAIL: gate should reject active worktree at 8-close"
  exit 1
fi
echo "OK gate rejects worktree_status=active"

cat > "$STATE" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `8-close` |
| review_status | done |
| review_skip_reason | — |
| code_changed | yes |
| review_round | `1` |
| last_reviewed_round | `1` |

## REVIEW_FINDINGS
| id | severity | finding | source | action | backlog_ref | status |
| ch-r1-001 | low | defer this | round-1 /code-review | backlog | — | open |
EOF

if python3 "${SCRIPTS}/validate_ritual_gate.py" \
  --project "$TMP" --loop-id code-health --state-file STATE.md --mode arm 2>/dev/null; then
  echo "FAIL: gate should reject backlog without backlog_ref"
  exit 1
fi
echo "OK gate rejects missing Phase 7b backlog_ref"

# Manifest stale at 8-close with git diff
GIT_TMP="$(mktemp -d)"
(
  cd "$GIT_TMP"
  git init -q
  git config user.email test@test.com
  git config user.name Test
  mkdir -p pwa
  echo "v1" > pwa/changed.ts
  git add .
  git commit -q -m init
  echo "v2" >> pwa/changed.ts
)
cat > "${GIT_TMP}/STATE.md" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `8-close` |
| review_status | done |
| review_round | `1` |
| last_reviewed_round | `1` |
| code_changed | yes |
| review_changed_files | `pwa/changed.ts` |
| review_fingerprint | `stalehash000000` |

## REVIEW_FINDINGS
| id | severity | finding | source | action | backlog_ref | status |
| wr-r1-001 | low | note pwa/changed.ts:1 | round-1 /code-review | closed | — | closed |
EOF

if python3 "${SCRIPTS}/validate_ritual_gate.py" \
  --project "$GIT_TMP" --loop-id worker-relay --state-file STATE.md --mode arm 2>/dev/null; then
  echo "FAIL: gate should reject stale manifest fingerprint"
  exit 1
fi
echo "OK gate rejects stale manifest"

# Sentinel-only with changed files
python3 - <<PY
import review_scope as rs
from pathlib import Path

root = Path("${GIT_TMP}")
live = rs.list_changed_files(root, ["pwa/"])
fp = rs.files_fingerprint(live)
state = f"""## CHECKPOINT
| Field | Value |
| phase | \`8-close\` |
| review_status | done |
| review_round | \`1\` |
| last_reviewed_round | \`1\` |
| code_changed | yes |
| review_changed_files | \`{' '.join(live)}\` |
| review_fingerprint | \`{fp}\` |

## REVIEW_FINDINGS
| id | severity | finding | source | action | backlog_ref | status |
| wr-r1-000 | low | No issues | round-1 /code-review | closed | — | closed |
"""
Path("${GIT_TMP}/STATE.md").write_text(state)
PY

if python3 "${SCRIPTS}/validate_ritual_gate.py" \
  --project "$GIT_TMP" --loop-id worker-relay --state-file STATE.md --mode arm 2>/dev/null; then
  echo "FAIL: gate should reject sentinel-only review with changed files"
  exit 1
fi
echo "OK gate rejects sentinel-only with changed files"
rm -rf "$GIT_TMP"

cat > "$STATE" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `9-arm` |
| review_status | skipped |
| review_skip_reason | test |
| code_changed | no |
EOF

python3 "${SCRIPTS}/validate_ritual_gate.py" \
  --project "$TMP" --loop-id worker-relay --state-file STATE.md --mode arm
echo "OK gate accepts 9-arm for recovery re-arm"

python3 "${SCRIPTS}/validate_ritual_gate.py" \
  --project "$TMP" --loop-id worker-relay --state-file STATE.md --mode steady
echo "OK steady mode accepts completed 9-arm"

PAYLOAD="$(python3 "${SCRIPTS}/build_wake_prompt.py" \
  --loop-id worker-relay \
  --contract-doc docs/window-instances/worker-relay/INSTANCE.md \
  --state-file docs/window-instances/worker-relay/STATE.md \
  --project "$(cd "$ROOT/../.." && pwd)" 2>/dev/null || true)"

if echo "$PAYLOAD" | grep -q '"allowed_phase": "1-wake"'; then
  echo "OK wake prompt uses allowed_phase 1-wake"
else
  echo "WARN: could not verify wake prompt in Habits project (optional)"
fi

echo "OK ritual gate segment"
