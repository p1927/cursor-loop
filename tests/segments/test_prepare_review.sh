#!/usr/bin/env bash
# Segment: prepare_review_tick + fresh-review gate
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPTS="${ROOT}/scripts"
HABITS="$(cd "$ROOT/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

export PYTHONPATH="${SCRIPTS}:${PYTHONPATH:-}"

STATE="${TMP}/STATE.md"
cat > "$STATE" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `8-close` |
| review_status | done |
| review_round | `0` |
| last_reviewed_round | `0` |
| code_changed | yes |
| review_skip_reason | — |

## REVIEW_FINDINGS
| id | severity | finding | source | action | backlog_ref | status |
| rf-r0-000 | low | No issues | round-0 /code-review | closed | — | closed |
EOF

# prepare_review_tick on isolated project (no git repo / no diff)
OUT="$(bash "${SCRIPTS}/prepare_review_tick.sh" "$TMP" \
  --state-file STATE.md --loop-id worker-relay)"
if echo "$OUT" | grep -q "PREPARE_REVIEW_BEGIN"; then
  echo "OK prepare_review_tick runs"
else
  echo "FAIL prepare_review_tick output: $OUT"
  exit 1
fi
if echo "$OUT" | grep -q "suggested_code_changed=no"; then
  echo "OK prepare_review_tick no-diff path"
fi

python3 - <<'PY'
import ritual_phase as rp
from pathlib import Path

state = """## CHECKPOINT
| Field | Value |
| phase | `8-close` |
| review_status | done |
| review_round | `0` |
| last_reviewed_round | `0` |
| code_changed | yes |

## REVIEW_FINDINGS
| id | severity | finding | source | action | backlog_ref | status |
| rf-r0-000 | low | No issues | round-0 /code-review | closed | — | closed |
"""
cp = rp.parse_checkpoint_table(state)
# Without project_root, stale done passes if round findings exist
r = rp.required_phase_before_arm(cp, state, mode="arm")
assert r.ok, "should pass without git cross-check when no project_root"

last = rp.max_reviewed_round(state)
assert last == 0, f"expected last_reviewed 0, got {last}"
print("OK max_reviewed_round and gate without git")
PY

cat > "$STATE" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `8-close` |
| review_status | done |
| review_round | `1` |
| code_changed | yes |

## REVIEW_FINDINGS
| id | severity | finding | source | action | backlog_ref | status |
| — | — | — | — | — | — | — |
EOF

if python3 "${SCRIPTS}/validate_ritual_gate.py" \
  --project "$TMP" --loop-id worker-relay --state-file STATE.md --mode arm 2>/dev/null; then
  echo "FAIL: gate should reject done without round-1 findings"
  exit 1
fi
echo "OK gate rejects missing round-N findings"

# --apply writes manifest fields
APPLY_TMP="$(mktemp -d)"
trap 'rm -rf "$TMP" "$APPLY_TMP"' EXIT
(
  cd "$APPLY_TMP"
  git init -q
  git config user.email test@test.com
  git config user.name Test
  mkdir -p pwa
  echo "v1" > pwa/apply.ts
  git add .
  git commit -q -m init
  echo "v2" >> pwa/apply.ts
)
cat > "${APPLY_TMP}/STATE.md" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `5-verify` |
| review_status | pending |
| review_round | `0` |
| last_reviewed_round | `0` |
| code_changed | no |
| review_changed_files | — |
| review_fingerprint | — |
EOF

bash "${SCRIPTS}/prepare_review_tick.sh" "$APPLY_TMP" \
  --state-file STATE.md --loop-id worker-relay --apply >/dev/null

python3 - <<PY
from pathlib import Path
text = Path("${APPLY_TMP}/STATE.md").read_text()
assert "review_changed_files" in text
assert "pwa/apply.ts" in text
assert "review_fingerprint" in text
assert "code_changed" in text and "yes" in text
print("OK prepare_review_tick --apply wrote manifest")
PY

echo "OK prepare review segment"
