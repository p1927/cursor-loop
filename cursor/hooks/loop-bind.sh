#!/usr/bin/env bash
# beforeSubmitPrompt — bind conversation to loop contract; honor stop loop.
set -euo pipefail

# shellcheck source=_common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"
cursor_loop_run_hook hook_bind.py
