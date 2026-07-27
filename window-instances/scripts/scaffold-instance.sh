#!/usr/bin/env bash
# Scaffold a new Window Instance from _template/
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scaffold-instance.sh <loop_id> [options]

Options:
  --archetype <engineer|designer|product|qa>   Required
  --interval <seconds>                         Default: 60
  --sentinel-tick <SENTINEL>                   Default: AGENT_LOOP_TICK_<UPPER_ID>
  --sentinel-wake <SENTINEL>                   Default: AGENT_LOOP_WAKE_<UPPER_ID>
  --summary <one-liner>                        INSTANCE summary
  --role <title>                               IDENTITY role
  --job <one-liner>                            IDENTITY job
  --dry-run                                    Print actions only
  --yes                                        Skip confirmation

Example:
  bash scripts/scaffold-instance.sh qa-relay \
    --archetype qa \
    --interval 180 \
    --sentinel-tick AGENT_LOOP_TICK_QA_RELAY \
    --sentinel-wake AGENT_LOOP_WAKE_QA_RELAY
EOF
  exit 1
}

LOOP_ID=""
ARCHETYPE=""
INTERVAL="60"
SENTINEL_TICK=""
SENTINEL_WAKE=""
SUMMARY="Window Instance agent"
ROLE="Agent"
JOB="Deliver one backlog item per tick"
DRY_RUN=false
YES=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archetype) ARCHETYPE="$2"; shift 2 ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    --sentinel-tick) SENTINEL_TICK="$2"; shift 2 ;;
    --sentinel-wake) SENTINEL_WAKE="$2"; shift 2 ;;
    --summary) SUMMARY="$2"; shift 2 ;;
    --role) ROLE="$2"; shift 2 ;;
    --job) JOB="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --yes) YES=true; shift ;;
    -h|--help) usage ;;
    *)
      if [[ -z "$LOOP_ID" ]]; then
        LOOP_ID="$1"
        shift
      else
        echo "Unknown arg: $1" >&2
        usage
      fi
      ;;
  esac
done

[[ -n "$LOOP_ID" ]] || usage
[[ -n "$ARCHETYPE" ]] || { echo "Error: --archetype required" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
TEMPLATE="$(cd "$(dirname "$0")/.." && pwd)/_template"
BUNDLE="$ROOT/docs/window-instances/$LOOP_ID"
MANIFEST="$ROOT/docs/window-instances/instances.manifest.json"

UPPER_ID="$(echo "$LOOP_ID" | tr '[:lower:]-' '[:upper:]_')"
[[ -n "$SENTINEL_TICK" ]] || SENTINEL_TICK="AGENT_LOOP_TICK_${UPPER_ID}"
[[ -n "$SENTINEL_WAKE" ]] || SENTINEL_WAKE="AGENT_LOOP_WAKE_${UPPER_ID}"

if [[ -d "$BUNDLE" ]]; then
  echo "Error: bundle already exists: $BUNDLE" >&2
  exit 1
fi

if [[ "$YES" != true && "$DRY_RUN" != true ]]; then
  echo "Create instance: $LOOP_ID (archetype=$ARCHETYPE)"
  read -r -p "Continue? [y/N] " ans
  [[ "$ans" == "y" || "$ans" == "Y" ]] || exit 0
fi

subst() {
  sed \
    -e "s|{{loop_id}}|$LOOP_ID|g" \
    -e "s|{{archetype}}|$ARCHETYPE|g" \
    -e "s|{{interval_sec}}|$INTERVAL|g" \
    -e "s|{{sentinel_tick}}|$SENTINEL_TICK|g" \
    -e "s|{{sentinel_wake}}|$SENTINEL_WAKE|g" \
    -e "s|{{summary_one_liner}}|$SUMMARY|g" \
    -e "s|{{role_title}}|$ROLE|g" \
    -e "s|{{job_one_liner}}|$JOB|g" \
    -e "s|{{skills_list}}|- (configure in IDENTITY.md)|g" \
    -e "s|{{reference_docs_list}}|- tools/cursor-loop/window-instances/SPEC.md|g" \
    -e "s|{{forbidden_extra}}||g" \
    -e "s|{{ritual_local_notes}}|(none)|g"
}

if [[ "$DRY_RUN" == true ]]; then
  echo "Would create: $BUNDLE"
  echo "Would append to: $MANIFEST"
  exit 0
fi

mkdir -p "$BUNDLE"
for f in INSTANCE.md IDENTITY.md RITUAL.md STATE.md; do
  subst < "$TEMPLATE/$f" > "$BUNDLE/$f"
done

python3 - "$MANIFEST" "$LOOP_ID" "$ARCHETYPE" "$BUNDLE" "$SENTINEL_TICK" "$SENTINEL_WAKE" "$INTERVAL" <<'PY'
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
loop_id, archetype, bundle, tick, wake, interval = sys.argv[2:8]
bundle_rel = str(Path(bundle).relative_to(manifest_path.parent.parent.parent))

data = json.loads(manifest_path.read_text())
entry = {
    "loop_id": loop_id,
    "archetype": archetype,
    "bundle": bundle_rel.replace("\\", "/"),
    "contract_doc": f"{bundle_rel.replace(chr(92), '/')}/INSTANCE.md",
    "state_file": f"{bundle_rel.replace(chr(92), '/')}/STATE.md",
    "sentinel": tick,
    "wake_sentinel": wake,
    "interval_sec": int(interval),
    "backlog_sections": ["BACKLOG"],
    "handoffs_out": [],
}
ids = {i["loop_id"] for i in data.get("instances", [])}
if loop_id in ids:
    raise SystemExit(f"loop_id already in manifest: {loop_id}")
data.setdefault("instances", []).append(entry)
manifest_path.write_text(json.dumps(data, indent=2) + "\n")
PY

chmod +x "$ROOT/tools/cursor-loop/scripts/instance-doctor.sh" 2>/dev/null || true

if ! python3 "$ROOT/tools/cursor-loop/scripts/validate_instance.py" "$ROOT"; then
  echo "Warning: validate_instance.py failed — fix bundle before binding" >&2
fi

echo ""
echo "Created: docs/window-instances/$LOOP_ID/"
echo "Paste:   @docs/window-instances/$LOOP_ID/INSTANCE.md keep working"
echo "Verify:  bash tools/cursor-loop/scripts/verify-wake.sh $LOOP_ID"
