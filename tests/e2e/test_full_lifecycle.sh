#!/usr/bin/env bash
# E2E: install → bind → start loop → verify → stop → force-reset → cleanup.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=../helpers/test_lib.sh
source "$(dirname "$0")/../helpers/test_lib.sh"

cleanup_e2e() {
  local project="${1:-}"
  if [[ -n "$project" && -d "$project" ]]; then
    test_cleanup_project "$project" 2>/dev/null || true
    test_rmdir "$project"
  fi
}

test_e2e_full_lifecycle() {
  local tmp loop_id cid project
  tmp="$(test_mkdir)"
  export TMPDIR="${tmp}/tmp"
  mkdir -p "$TMPDIR"
  project="${tmp}/project"
  mkdir -p "$project"
  loop_id="e2e-$$"
  cid="e2e-chat-$$"

  trap 'cleanup_e2e "$tmp"' EXIT

  bash "${ROOT}/install.sh" "$project" --copy --package-path vendor/cursor-loop >/dev/null

  mkdir -p "${project}/docs/agents"
  cat > "${project}/docs/agents/e2e-loop.md" <<EOF
# E2E loop

## Loop config

| Field | Value |
|-------|-------|
| loop_id | \`${loop_id}\` |
| sentinel | \`AGENT_LOOP_TICK_E2E\` |
| wake_sentinel | \`AGENT_LOOP_WAKE_E2E\` |
| interval_sec | \`3600\` |
| monitor_regex | \`^AGENT_LOOP_TICK_E2E\` |
| loop_script | \`vendor/cursor-loop/scripts/agent-loop.sh\` |
| contract_doc | \`docs/agents/e2e-loop.md\` |

## Task

E2E test task.
EOF

  bind_payload="{\"conversation_id\":\"${cid}\",\"workspace_roots\":[\"${project}\"],\"prompt\":\"@docs/agents/e2e-loop.md keep working\"}"
  echo "$bind_payload" | bash "${project}/.cursor/hooks/loop-bind.sh"
  test -f "${project}/.cursor/loop-bindings/${cid}.json"

  LOOP_ID="$loop_id" SENTINEL="AGENT_LOOP_TICK_E2E" INTERVAL=3600 PROMPT='e2e' \
    bash "${project}/vendor/cursor-loop/scripts/agent-loop.sh" &
  local loop_pid=$!
  sleep 0.5

  bash "${ROOT}/scripts/verify-loop.sh" "$loop_id"

  stop_payload="{\"conversation_id\":\"${cid}\",\"workspace_roots\":[\"${project}\"],\"prompt\":\"stop loop\"}"
  echo "$stop_payload" | bash "${project}/.cursor/hooks/loop-bind.sh"
  grep -q '"stopped": true' "${project}/.cursor/loop-bindings/${cid}.json"

  kill -TERM "$loop_pid" 2>/dev/null || true
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    kill -0 "$loop_pid" 2>/dev/null || break
    sleep 0.1
  done
  kill -9 "$loop_pid" 2>/dev/null || true
  wait "$loop_pid" 2>/dev/null || true
  rm -f "${TMPDIR}/cursor-loop-${loop_id}.pid"

  python3 "${ROOT}/scripts/force_reset.py" "$project" --all --yes --json >/dev/null
  test ! -f "${project}/.cursor/loop-bindings/${cid}.json"

  python3 "${ROOT}/scripts/validate_contracts.py" "$project"

  trap - EXIT
  cleanup_e2e "$tmp"
  echo "PASS e2e_full_lifecycle"
}

test_e2e_full_lifecycle
