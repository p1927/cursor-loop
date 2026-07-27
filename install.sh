#!/usr/bin/env bash
# Install cursor-loop into a consumer project.
#
# Usage:
#   ./install.sh TARGET [options]
#
# Options:
#   --symlink          Symlink rule + hooks to package (default)
#   --copy             Copy package to TARGET/PACKAGE_PATH and copy rule + hooks
#   --package-path P   Package location relative to TARGET (default: tools/cursor-loop)
#   --contracts-dir D  Contracts directory (default: docs/agents)
#   --uninstall        Remove cursor-loop Cursor artifacts from TARGET
#   --help             Show help
set -euo pipefail

PACKAGE_DIR="$(cd "$(dirname "$0")" && pwd)"
VERSION="$(cat "${PACKAGE_DIR}/VERSION" 2>/dev/null || echo "0.0.0")"

MODE="symlink"
TARGET=""
PACKAGE_PATH="tools/cursor-loop"
CONTRACTS_DIR="docs/agents"
UNINSTALL=0

usage() {
  sed -n '2,14p' "$0"
}

args=("$@")
for ((i = 0; i < ${#args[@]}; i++)); do
  arg="${args[i]}"
  case "$arg" in
    --symlink) MODE="symlink" ;;
    --copy) MODE="copy" ;;
    --uninstall) UNINSTALL=1 ;;
    --help|-h) usage; exit 0 ;;
    --package-path)
      PACKAGE_PATH="${args[i + 1]:?Missing value for --package-path}"
      ((i++))
      ;;
    --contracts-dir)
      CONTRACTS_DIR="${args[i + 1]:?Missing value for --contracts-dir}"
      ((i++))
      ;;
    *)
      if [[ -z "$TARGET" && "$arg" != --* ]]; then
        TARGET="$arg"
      fi
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  usage >&2
  exit 1
fi

if ! command -v bash >/dev/null 2>&1; then
  echo "bash is required" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required for cursor-loop hooks" >&2
  exit 1
fi

TARGET="$(cd "$TARGET" && pwd)"

if [[ "$UNINSTALL" -eq 1 ]]; then
  rm -f "${TARGET}/.cursor/rules/agent-loop-contract.mdc"
  rm -f "${TARGET}/.cursor/hooks/loop-bind.sh" \
        "${TARGET}/.cursor/hooks/loop-survival.sh" \
        "${TARGET}/.cursor/hooks/_common.sh"
  rm -f "${TARGET}/.cursor/cursor-loop.json"
  echo "Removed cursor-loop Cursor artifacts from ${TARGET}"
  echo "NOTE: hooks.json entries and package at ${PACKAGE_PATH} were not removed."
  exit 0
fi

DEST_PACKAGE="${TARGET}/${PACKAGE_PATH}"

if [[ "$MODE" == "copy" ]]; then
  mkdir -p "$(dirname "$DEST_PACKAGE")"
  rsync -a --delete \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    "${PACKAGE_DIR}/" "${DEST_PACKAGE}/"
  echo "copied package: ${DEST_PACKAGE}"
  INSTALL_PACKAGE="${DEST_PACKAGE}"
else
  INSTALL_PACKAGE="${PACKAGE_DIR}"
fi

PKG_REL="$(python3 -c "import os; print(os.path.relpath('${INSTALL_PACKAGE}', '${TARGET}'))")"

RULE_SRC="${INSTALL_PACKAGE}/cursor/rules/agent-loop-contract.mdc"
RULE_DEST="${TARGET}/.cursor/rules/agent-loop-contract.mdc"
HOOK_DEST_DIR="${TARGET}/.cursor/hooks"

install_file() {
  local src="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [[ "$MODE" == "symlink" ]]; then
    ln -sf "$src" "$dest"
    echo "symlink: $dest -> $src"
  else
    cp "$src" "$dest"
    echo "copy: $dest"
  fi
}

mkdir -p "${TARGET}/.cursor/rules" "${HOOK_DEST_DIR}" "${TARGET}/.cursor/loop-bindings"

install_file "${INSTALL_PACKAGE}/cursor/rules/agent-loop-contract.mdc" "$RULE_DEST"
install_file "${INSTALL_PACKAGE}/cursor/hooks/_common.sh" "${HOOK_DEST_DIR}/_common.sh"
install_file "${INSTALL_PACKAGE}/cursor/hooks/loop-bind.sh" "${HOOK_DEST_DIR}/loop-bind.sh"
install_file "${INSTALL_PACKAGE}/cursor/hooks/loop-survival.sh" "${HOOK_DEST_DIR}/loop-survival.sh"

chmod +x \
  "${HOOK_DEST_DIR}/_common.sh" \
  "${HOOK_DEST_DIR}/loop-bind.sh" \
  "${HOOK_DEST_DIR}/loop-survival.sh" \
  "${INSTALL_PACKAGE}/scripts/agent-loop.sh" \
  "${INSTALL_PACKAGE}/scripts/loop-status.sh" \
  "${INSTALL_PACKAGE}/scripts/hook_bind.py" \
  "${INSTALL_PACKAGE}/scripts/hook_survival.py" \
  "${INSTALL_PACKAGE}/scripts/merge_hooks.py" \
  "${INSTALL_PACKAGE}/scripts/cleanup_bindings.py" \
  "${INSTALL_PACKAGE}/scripts/doctor.sh"

MANIFEST="${TARGET}/.cursor/cursor-loop.json"
cat > "$MANIFEST" <<EOF
{
  "version": "${VERSION}",
  "package_root": "${PKG_REL}",
  "contracts_dir": "${CONTRACTS_DIR}",
  "contract_globs": [],
  "binding_ttl_days": 30
}
EOF
echo "wrote: ${MANIFEST}"

HOOKS_JSON="${TARGET}/.cursor/hooks.json"
SNIPPET="${INSTALL_PACKAGE}/cursor/hooks/hooks.json.snippet"
python3 "${INSTALL_PACKAGE}/scripts/merge_hooks.py" "$HOOKS_JSON" "$SNIPPET"
echo "merged: ${HOOKS_JSON}"

mkdir -p "${TARGET}/${CONTRACTS_DIR}"
if [[ ! -f "${TARGET}/docs/START_LOOPS.md" ]]; then
  cp "${INSTALL_PACKAGE}/template/START_LOOPS.template.md" "${TARGET}/docs/START_LOOPS.md"
  echo "created: ${TARGET}/docs/START_LOOPS.md"
fi

if [[ -f "${TARGET}/.gitignore" ]] && ! grep -q 'loop-bindings' "${TARGET}/.gitignore" 2>/dev/null; then
  printf '\n.cursor/loop-bindings/\n' >> "${TARGET}/.gitignore"
  echo "appended: .cursor/loop-bindings/ to .gitignore"
fi

cat <<EOF

cursor-loop v${VERSION} installed into: ${TARGET}
  mode:     ${MODE}
  rule:     ${RULE_DEST}
  hooks:    ${HOOK_DEST_DIR}/loop-bind.sh
            ${HOOK_DEST_DIR}/loop-survival.sh
  manifest: ${MANIFEST}
  package:  ${PKG_REL}

Next: @${CONTRACTS_DIR}/<task>.md keep working
EOF
