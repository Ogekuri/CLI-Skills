"""
@file settings.py
@brief Persist enabled CLI targets.
@details User configuration is a JSON object stored at
         `$HOME/.config/cli-skills/config.json` with the schema
         `{"enabled": ["<cli>", ...]}`.
         Loading tolerates missing, unreadable, or malformed content by
         returning normalized defaults.
@satisfies DES-047 DES-048
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any

## @brief Configuration path relative to the user home directory.
# @details `$HOME` + `.config/cli-skills/config.json`.
# @satisfies DES-047
CONFIG_RELATIVE = Path(".config") / "cli-skills" / "config.json"


def config_path(home: Path | None = None) -> Path:
    """
    @brief Resolve the user configuration file path.
    @details Joins the effective home directory with `.config/cli-skills/config.json`.
    @param home {Path | None} Optional home-directory override.
    @return {Path} Configuration file path.
    @satisfies DES-047
    """
    base = Path.home() if home is None else home
    return base / CONFIG_RELATIVE


def _unique_strings(value: Any) -> list[str]:
    """
    @brief Filter an arbitrary JSON value into unique non-empty strings.
    @details Preserves first-seen order and drops non-string, empty, and
             duplicate entries.
    @param value {Any} Candidate JSON value.
    @return {list[str]} Unique strings in first-seen order; empty for
            non-list input.
    @complexity O(n) where n is the list length.
    @satisfies DES-048
    """
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item and item not in result:
            result.append(item)
    return result


def load_config(home: Path | None = None) -> dict[str, Any]:
    """
    @brief Load the user configuration with normalized defaults.
    @details Reads JSON from `config_path`. Missing, unreadable, non-object, or
             malformed content yields `{"enabled": []}`.
             Valid `enabled` entries are unique strings.
    @param home {Path | None} Optional home-directory override.
    @return {dict[str, Any]} Normalized configuration object.
    @note Read and decode errors are handled internally and are not raised.
    @satisfies DES-047 DES-048
    """
    default: dict[str, Any] = {"enabled": []}
    try:
        raw = json.loads(config_path(home).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default
    if not isinstance(raw, dict):
        return default
    return {"enabled": _unique_strings(raw.get("enabled"))}


def save_config(config: dict[str, Any], home: Path | None = None) -> Path:
    """
    @brief Persist normalized configuration to the user configuration file.
    @details Creates parent directories, serializes with two-space indentation
             and a trailing newline, writes a unique sibling temporary file,
             flushes and fsyncs it, preserves the existing file mode, and
             replaces the target atomically. The parent directory is fsynced
             when the platform allows it. A failed write removes the temporary
             file so the previous configuration survives unchanged.
    @param config {dict[str, Any]} Configuration object to persist.
    @param home {Path | None} Optional home-directory override.
    @return {Path} Written configuration file path.
    @throws {OSError} When directory creation, writing, syncing, or replacing fails.
    @post The configuration file contains the serialized `config` object.
    @satisfies DES-047 DES-048 DES-113 DES-114
    """
    path = config_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(config, indent=2, ensure_ascii=False) + "\n"
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
        os.replace(temporary, path)
        _sync_directory(path.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return path


def _sync_directory(directory: Path) -> None:
    """
    @brief Flush a directory entry to disk when the platform supports it.
    @details Opens the directory read-only and fsyncs it; unsupported platforms
             and permission errors are ignored because the file data is already
             durable and the replacement is already atomic.
    @param directory {Path} Directory containing the replaced configuration file.
    @return {None}
    @satisfies DES-113
    """
    try:
        descriptor = os.open(str(directory), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)
