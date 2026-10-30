# skills (0.0.0)

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-GPL--3.0-491?style=flat-square" alt="License: GPL-3.0">
  <img src="https://img.shields.io/badge/platform-Linux-6A7EC2?style=flat-square&logo=terminal&logoColor=white" alt="Platforms">
  <img src="https://img.shields.io/badge/docs-live-b31b1b" alt="Docs">
<img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
</p>
<p align="center">
<strong>TODO: fill one-line very short program's description.</strong><br>
TODO: fill full multi-line program's description with brief recap of main features.
</p>


<p align="center">
  <a href="#quick-start">Quick Start</a> |
  <a href="#feature-highlights">Feature Highlights</a> |
  <a href="#acknowledgments">Acknowledgments</a>
</p>

<p align="center">
<br>
🚧 <strong>DRAFT</strong>: 👾 Alpha Development 👾 - Work in Progress 🏗️ 🚧<br>
⚠️ <strong>IMPORTANT NOTICE</strong>: Created with <a href="https://github.com/ogekuri/useReq"><strong>useReq/req</strong></a> 🤖✨ ⚠️<br>
<br>
<p>


## Feature Highlights
- TODO: fill bullet list with highlihts of main fetures
- 



## Quick Start

1. TODO: fill stes to quick start with program



## Usage

TODO: fill usage section

- 



## Install with Astral uv

#### Install
```bash
uv tool install skills --force --from git+https://github.com/Ogekuri/SKILLs.git
```

#### Uninstall
```bash
uv tool uninstall skills
```

## Live execution with uvx

Run skills directly from the current repository checkout without prior installation:

```bash
uvx --from git+https://github.com/Ogekuri/SKILLs.git skills
```

You can pass options as usual, for example:

```bash
uvx --from git+https://github.com/Ogekuri/SKILLs.git skills <args>
```


## Acknowledgments

TODO: fill scknowledgments section

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
