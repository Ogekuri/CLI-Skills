# skills (0.0.0)

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-GPL--3.0-491?style=flat-square" alt="License: GPL-3.0">
  <img src="https://img.shields.io/badge/platform-Linux-6A7EC2?style=flat-square&logo=terminal&logoColor=white" alt="Platforms">
  <img src="https://img.shields.io/badge/docs-live-b31b1b" alt="Docs">
<img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
</p>
<p align="center">
<strong>Install and update LLM agent skills and prompts for supported CLI tools.</strong><br>
Manage user-level skills and prompt templates for <code>pi</code>, <code>openclaw</code>, <code>codex</code>, <code>antigravity</code>, and <code>claude</code>.
</p>


<p align="center">
  <a href="#feature-highlights">Feature Highlights</a> |
  <a href="#quick-start">Quick Start</a> |
  <a href="#commands">Commands</a> |
  <a href="#supported-cli-targets">CLI Targets</a> |
  <a href="#install-behavior">Install Behavior</a> |
  <a href="#configuration">Configuration</a>
</p>
<p align="center">
  <a href="#release-checks">Release Checks</a> |
  <a href="#install-with-astral-uv">Install with Astral uv</a> |
  <a href="#live-execution-with-uvx">Live execution with uvx</a> |
  <a href="#local-execution">Local Execution</a> |
  <a href="#development">Development</a> |
  <a href="#acknowledgments">Acknowledgments</a>
</p>

<p align="center">
<br>
🚧 <strong>DRAFT</strong>: 👾 Alpha Development 👾 - Work in Progress 🏗️ 🚧<br>
⚠️ <strong>IMPORTANT NOTICE</strong>: Created with <a href="https://github.com/ogekuri/useReq"><strong>useReq/req</strong></a> 🤖✨ ⚠️<br>
<br>
<p>


## Feature Highlights

- Install bundled skills into each enabled CLI's user-level skills directory.
- Install manifest-listed prompt templates for `pi` and `claude`.
- Replace managed skill directories on every install and remove files that are no longer packaged.
- Enable or disable each target CLI; the selection persists in `~/.config/skills/config.json`.
- Check GitHub releases automatically with a 2-second timeout and a cached idle delay.
- Run from a repository checkout, as a uv tool, or with uvx.

Bundled skills:

- `astra-uv-project` - create a new Astral uv Python CLI project from scratch.
- `prompt-skill-architect` - create, review, and optimize LLM agent prompts and skills.


## Quick Start

Prerequisites: Python 3.11 or newer and [Astral uv](https://docs.astral.sh/uv/).

1. Install the CLI:

   ```bash
   uv tool install skills --force --from git+https://github.com/Ogekuri/SKILLs.git
   ```

2. Enable one or more target CLIs:

   ```bash
   skills enable pi
   skills enable claude
   ```

3. Install the bundled resources:

   ```bash
   skills install
   ```

4. Start or restart the target CLI so it discovers the installed skills.

`enable` and `disable` persist their selection; `install` updates every enabled CLI.


## Commands

| Command | Behavior |
|---|---|
| `skills` | Print the full help screen. |
| `skills --help` | Print the full help screen. |
| `skills <command> --help` | Print help for `enable`, `disable`, `install`, `--upgrade`, `--uninstall`, `--ver`, or `--version`. |
| `skills --ver` | Print the installed version as `x.y.z` and force a release check. |
| `skills --version` | Print the installed version as `x.y.z` and force a release check. |
| `skills --upgrade` | Reinstall the tool with uv on Linux; print the manual command on other platforms. |
| `skills --uninstall` | Uninstall the tool with uv on Linux; print the manual command on other platforms. |
| `skills enable <cli name>` | Enable skill and prompt installation for a supported CLI. |
| `skills disable <cli name>` | Disable skill and prompt installation for a supported CLI. |
| `skills install` | Install or update bundled skills and prompts for every enabled CLI. |

Exit codes:

- `0` - success, including `install` with no enabled CLI.
- `1` - installation failed for at least one enabled CLI.
- `2` - unknown command or option, unsupported CLI name, or missing CLI name.


## Supported CLI Targets

| CLI | Skills directory | Prompts directory |
|---|---|---|
| `pi` | `~/.pi/agent/skills` | `~/.pi/agent/prompts` |
| `openclaw` | `~/.openclaw/workspace/skills` | Not supported |
| `codex` | `~/.codex/skills` | Not supported |
| `antigravity` | `~/.gemini/config/skills` | Not supported |
| `claude` | `~/.claude/skills` | `~/.claude/commands` |

Only enabled CLIs are updated. Destinations are user-level configuration directories, not project directories.

Only manifest-listed prompt files are installed; the current package contains no prompt templates.


## Install Behavior

- `install` processes every enabled CLI.
- Each packaged skill is copied to `<skills directory>/<skill name>`.
- Existing skill files are overwritten with the packaged versions.
- Files and directories inside a managed skill directory that are absent from the package are deleted.
- Skill directories not managed by the package are left unchanged.
- Previously installed prompt files that are no longer packaged are deleted.
- A missing packaged source path aborts that CLI and reports an error; remaining enabled CLIs are still processed.
- Output reports the installed skill and prompt counts for each processed CLI.
- With no enabled CLI, `install` prints an informational message and exits with `0`.
- If any CLI installation fails, `install` prints the error and exits with `1`.


## Configuration

The CLI stores its user configuration at:

```text
~/.config/skills/config.json
```

Example:

```json
{
  "enabled": [
    "pi",
    "claude"
  ]
}
```

`enable` and `disable` maintain the `enabled` array. The file may also contain prompt installation records, which are maintained automatically; edit only `enabled` when changing the configuration manually. A missing or invalid file is treated as an empty configuration.


## Release Checks

- A release check runs before command dispatch.
- The check requests the latest GitHub release with a 2-second timeout.
- Cache file: `~/.cache/skills/check_version_idle-time.json`.
- The check is skipped while the cached idle time is valid.
- `--ver` and `--version` force a check regardless of the cache.
- A newer release prints a bright-green message and sets a 3600-second idle delay.
- A failed check or no newer release prints a bright-red message and sets an 86400-second idle delay.
- Notifications are written to stderr.


## Install with Astral uv

Install:

```bash
uv tool install skills --force --from git+https://github.com/Ogekuri/SKILLs.git
```

Upgrade through the CLI:

```bash
skills --upgrade
```

Uninstall through the CLI:

```bash
skills --uninstall
```

Manual uninstall:

```bash
uv tool uninstall skills
```

`skills --upgrade` and `skills --uninstall` run the corresponding uv tool command on Linux. On other platforms they print the command for manual execution.


## Live execution with uvx

Run `skills` from the repository without installing the tool:

```bash
uvx --from git+https://github.com/Ogekuri/SKILLs.git skills --help
```

Use the same form for installation commands, for example:

```bash
uvx --from git+https://github.com/Ogekuri/SKILLs.git skills install
```


## Local Execution

Run the CLI from the repository checkout:

```bash
./scripts/skills.sh --help
./scripts/skills.sh enable pi
./scripts/skills.sh install
```

The launcher delegates execution to Astral uv from the repository root.


## Development

Run the tests:

```bash
uv run python -m unittest discover -s tests
```

Build distributions:

```bash
uv run --frozen --with build python -m build
```


## Acknowledgments

Uses [Astral uv](https://docs.astral.sh/uv/) for packaging and execution and the [Agent Skills](https://agentskills.io/specification) directory format for bundled resources.
