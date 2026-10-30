# skills

Agent skills and prompts: a Python CLI distributed with Astral uv and uvx.

## Usage

```bash
./scripts/skills.sh --help
./scripts/skills.sh --version
```

The CLI checks GitHub releases before dispatching commands. Version checks use a two-second timeout and a cache at `~/.cache/skills/check_version_idle-time.json`. `--ver` and `--version` always force a check. Notifications are written to stderr.

`--upgrade` and `--uninstall` run the corresponding uv tool command on Linux. On other operating systems they print the command for manual execution.

## Install

```bash
uv tool install skills --force --from git+https://github.com/Ogekuri/SKILLs.git
```

## Run without installing

```bash
uvx --from git+https://github.com/Ogekuri/SKILLs.git skills --help
```

## Uninstall

```bash
uv tool uninstall skills
```

## Development

Run the tests with `uv run python -m unittest discover -s tests` and build distributions with `uv run --frozen --with build python -m build`.
