# Minimal cursor-loop consumer project

This example shows the smallest useful setup: one contract, one loop.

## Try it

From the **cursor-loop repo root**:

```bash
bash examples/minimal-project/setup.sh
```

Then open this folder in Cursor and paste in Agent chat:

```text
@docs/agents/hello-loop.md keep working
```

## What's included

| Path | Purpose |
|------|---------|
| `docs/agents/hello-loop.md` | Loop contract (60s tick) |
| `docs/START_LOOPS.md` | Paste cheat sheet |
| `vendor/cursor-loop/` | Package (created by `setup.sh --copy`) |
| `.cursor/` | Rule, hooks, manifest (created by `setup.sh`) |

## Reset

```bash
bash vendor/cursor-loop/install.sh . --uninstall
rm -rf vendor/cursor-loop .cursor docs
```

## Remote install (no git submodule)

From any empty directory:

```bash
curl -fsSL https://raw.githubusercontent.com/p1927/cursor-loop/v0.2.0/install-remote.sh | bash -s -- .
cp -R /path/to/cursor-loop/template/AGENT_LOOP_TEMPLATE.md docs/agents/hello-loop.md
# edit contract, then paste @docs/agents/hello-loop.md keep working
```
