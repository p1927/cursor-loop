#!/usr/bin/env bash
# stop hook backup — re-arm only if bound, not stopped, and pidfile process is dead.
set -euo pipefail

# shellcheck source=_common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"
cursor_loop_run_hook hook_survival.py
