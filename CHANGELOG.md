# Changelog

## 0.1.0

- Initial standalone release
- Manifest-driven hook bootstrap (`package_root`, `contracts_dir`)
- Python hook entrypoints (`hook_bind.py`, `hook_survival.py`)
- Stop flow: `stopped` flag on binding; survival hook respects it
- `install.sh`: `--symlink`, `--copy`, `--package-path`, `--contracts-dir`, `--uninstall`
- Idempotent `hooks.json` merge via `merge_hooks.py`
- JSON-safe tick payloads in `agent-loop.sh`
- `loop-status.sh --json` and `--loop-id`
- `doctor.sh` health check
