"""
@file configops.py
@brief Validated, atomic configuration reads and mutations over the canonical schema.
@details Every configuration command bootstraps the global configuration file
         from schema defaults when it is missing, resolves canonical paths
         through `schema.parse_path`, validates the whole resulting
         configuration with `schema.validate_config`, and persists it through
         the atomic writer in `settings.save_config`. Reads tolerate malformed
         content; mutations fail without writing when the stored configuration
         or the requested operation violates the schema.
@satisfies DES-104 DES-109 DES-111 DES-112 DES-113 DES-114 DES-134 DES-135
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from . import schema, settings


class ConfigError(RuntimeError):
    """
    @brief Signal a configuration read, resolution, or persistence failure.
    @details Converted by the CLI layer into a stderr diagnostic and exit
             status 1. No configuration mutation has occurred when raised.
    @satisfies DES-109 DES-114 DES-117
    """


def ensure_initialized(home: Path | None = None) -> Path:
    """
    @brief Create the configuration directory and file from schema defaults.
    @details Existing files are never overwritten, so a valid configuration
             survives every configuration command.
    @param home {Path | None} Optional home-directory override.
    @return {Path} Existing or newly initialized configuration file path.
    @throws {OSError} When directory creation or initialization writing fails.
    @satisfies DES-111
    """
    path = settings.config_path(home)
    if not path.exists():
        try:
            settings.save_config(schema.default_config(), home)
        except OSError as exc:
            raise ConfigError(f"Cannot initialize configuration file '{path}': {exc}") from exc
    return path


def read_config(home: Path | None = None) -> dict[str, Any]:
    """
    @brief Read the configuration with normalized defaults for display commands.
    @details Bootstraps a missing file, then delegates to the tolerant loader so
             `--print`, `--info`, and `--get` never fail on foreign content.
    @param home {Path | None} Optional home-directory override.
    @return {dict[str, Any]} Normalized configuration object.
    @throws {OSError} When the configuration cannot be initialized.
    @satisfies DES-111 DES-115 DES-132
    """
    ensure_initialized(home)
    return settings.load_config(home)


def read_raw(home: Path | None = None) -> bytes:
    """
    @brief Read the unmodified on-disk configuration bytes.
    @details Bootstraps a missing file from schema defaults, then returns the
             stored bytes without parsing, reformatting, or tree decoration.
    @param home {Path | None} Optional home-directory override.
    @return {bytes} Raw configuration file content.
    @throws {OSError} When initialization or reading fails.
    @satisfies DES-111 DES-116
    """
    return ensure_initialized(home).read_bytes()


def read_strict(home: Path | None = None) -> dict[str, Any]:
    """
    @brief Read and strictly validate the configuration before a mutation.
    @details Bootstraps a missing file, decodes the stored JSON, and rejects
             malformed payloads, unknown keys, and invalid values.
    @param home {Path | None} Optional home-directory override.
    @return {dict[str, Any]} Schema-valid configuration object.
    @throws {ConfigError} When the file is unreadable, undecodable, or schema-invalid.
    @satisfies DES-112 DES-114
    """
    path = ensure_initialized(home)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigError(f"Cannot read configuration file '{path}': {exc}") from exc
    try:
        return schema.validate_config(payload)
    except schema.SchemaError as exc:
        raise ConfigError(f"Invalid configuration file '{path}': {exc}") from exc


def get_value(config: dict[str, Any], path: schema.Path) -> Any:
    """
    @brief Read the value addressed by a resolved path.
    @details Rejects array operations, unknown keys, and out-of-range indices
             before returning the value. Complexity O(S) over path steps.
    @param config {dict[str, Any]} Configuration object.
    @param path {schema.Path} Resolved canonical path.
    @return {Any} Addressed JSON value.
    @throws {ConfigError} For array operations or missing/out-of-range targets.
    @satisfies DES-109 DES-110 DES-115 DES-134
    """
    return _navigate(config, path, path.steps)


def apply_set(config: dict[str, Any], path: schema.Path, text: str) -> dict[str, Any]:
    """
    @brief Apply one `--set` operation and return a new configuration object.
    @details Parses the argument into the schema type of the addressed node,
             replaces, appends, or inserts exactly one value, then validates the
             whole result. The input object is never mutated.
    @param config {dict[str, Any]} Current schema-valid configuration.
    @param path {schema.Path} Resolved canonical path.
    @param text {str} Raw command-line value.
    @return {dict[str, Any]} New validated configuration object.
    @throws {schema.SchemaError} When the value violates the schema.
    @throws {ConfigError} When the path cannot be navigated or an index is out of range.
    @satisfies DES-110 DES-112 DES-129 DES-134 DES-135
    """
    value = schema.coerce_value(path.node, text, path.display)
    updated = copy.deepcopy(config)
    if not path.steps:
        return schema.validate_config(value)
    last = path.steps[-1]
    container = _navigate(updated, path, path.steps[:-1])
    if last.kind == schema.STEP_TOKEN:
        if not isinstance(container, dict):
            raise ConfigError(f"Path '{path.display}' does not address a configuration key.")
        container[last.token] = value
    elif last.kind == schema.STEP_INDEX:
        if not isinstance(container, list):
            raise ConfigError(f"Path '{path.display}' does not address an array element.")
        _check_index(path, last, len(container), insert=False)
        container[last.index] = value
    elif last.kind == schema.STEP_APPEND:
        if not isinstance(container, list):
            raise ConfigError(f"Path '{path.display}' does not address an array.")
        container.append(value)
    elif last.kind == schema.STEP_INSERT:
        if not isinstance(container, list):
            raise ConfigError(f"Path '{path.display}' does not address an array.")
        _check_index(path, last, len(container), insert=True)
        container.insert(last.index, value)
    else:
        raise ConfigError(f"Path '{path.display}' uses an unsupported operation.")
    return schema.validate_config(updated)


def apply_unset(config: dict[str, Any], path: schema.Path) -> dict[str, Any]:
    """
    @brief Apply one `--unset` operation and return a new configuration object.
    @details Array indices delete exactly one element and compact later indices;
             resettable values restore the declared schema default. Values
             without a schema default are rejected. The input object is never
             mutated.
    @param config {dict[str, Any]} Current schema-valid configuration.
    @param path {schema.Path} Resolved canonical path.
    @return {dict[str, Any]} New validated configuration object.
    @throws {ConfigError} For array operations, missing targets, out-of-range
             indices, and values without a declared default.
    @satisfies DES-114 DES-128 DES-134 DES-135
    """
    updated = copy.deepcopy(config)
    if not path.steps:
        return schema.default_config()
    last = path.steps[-1]
    if last.kind in (schema.STEP_APPEND, schema.STEP_INSERT):
        raise ConfigError(f"Path '{path.display}' is an array operation and cannot be reset.")
    container = _navigate(updated, path, path.steps[:-1])
    if last.kind == schema.STEP_INDEX:
        if not isinstance(container, list):
            raise ConfigError(f"Path '{path.display}' does not address an array element.")
        _check_index(path, last, len(container), insert=False)
        del container[last.index]
        return schema.validate_config(updated)
    if not isinstance(container, dict) or last.token not in container:
        raise ConfigError(f"Path '{path.display}' does not address a configuration key.")
    if not schema.has_default(path.node):
        raise ConfigError(f"Path '{path.display}' has no schema default and cannot be reset; set an explicit value instead.")
    container[last.token] = schema.default_value(path.node)
    return schema.validate_config(updated)


def set_path(path_text: str, value_text: str, home: Path | None = None) -> schema.Path:
    """
    @brief Resolve one `--set` path, validate the result, and persist atomically.
    @details Reads the configuration strictly, applies the operation in memory,
             and writes only after full schema validation succeeds.
    @param path_text {str} Canonical colon-separated path.
    @param value_text {str} Raw command-line value.
    @param home {Path | None} Optional home-directory override.
    @return {schema.Path} Resolved path that was written.
    @throws {ConfigError} When resolution, validation, or persistence fails.
    @satisfies DES-111 DES-112 DES-113 DES-114
    """
    path = _parse(path_text)
    config = read_strict(home)
    try:
        updated = apply_set(config, path, value_text)
    except schema.SchemaError as exc:
        raise ConfigError(str(exc)) from exc
    try:
        settings.save_config(updated, home)
    except OSError as exc:
        raise ConfigError(f"Cannot write configuration file: {exc}") from exc
    return path


def unset_path(path_text: str, home: Path | None = None) -> schema.Path:
    """
    @brief Resolve one `--unset` path, validate the result, and persist atomically.
    @details Reads the configuration strictly, applies the reset or deletion in
             memory, and writes only after full schema validation succeeds.
    @param path_text {str} Canonical colon-separated path.
    @param home {Path | None} Optional home-directory override.
    @return {schema.Path} Resolved path that was written.
    @throws {ConfigError} When resolution, validation, or persistence fails.
    @satisfies DES-111 DES-113 DES-114 DES-128
    """
    path = _parse(path_text)
    config = read_strict(home)
    try:
        updated = apply_unset(config, path)
    except schema.SchemaError as exc:
        raise ConfigError(str(exc)) from exc
    try:
        settings.save_config(updated, home)
    except OSError as exc:
        raise ConfigError(f"Cannot write configuration file: {exc}") from exc
    return path


def _parse(path_text: str) -> schema.Path:
    """
    @brief Resolve a canonical path and normalize schema errors.
    @details Keeps the public operation API uniform: every resolution failure
             surfaces as `ConfigError` instead of a raw `SchemaError`.
    @param path_text {str} Canonical colon-separated path.
    @return {schema.Path} Resolved path.
    @throws {ConfigError} When the path is empty or schema-invalid.
    @satisfies DES-109 DES-117
    """
    try:
        return schema.parse_path(path_text)
    except schema.SchemaError as exc:
        raise ConfigError(str(exc)) from exc


def _navigate(config: dict[str, Any], path: schema.Path, steps: tuple[schema.Step, ...]) -> Any:
    """
    @brief Walk resolved path steps over the configuration object.
    @details Token steps index mappings; index steps index arrays with bounds
             validation; append and insert steps are rejected as unreadable.
    @param config {dict[str, Any]} Configuration object.
    @param path {schema.Path} Owning path used in diagnostics.
    @param steps {tuple[schema.Step, ...]} Steps to consume.
    @return {Any} Value or container reached by the steps.
    @throws {ConfigError} For missing keys, non-container values, operations,
             and out-of-range indices.
    @satisfies DES-109 DES-110 DES-134
    """
    current: Any = config
    for step in steps:
        if step.kind == schema.STEP_TOKEN:
            if not isinstance(current, dict) or step.token not in current:
                raise ConfigError(f"Missing key '{step.token}' in path '{path.display}'.")
            current = current[step.token]
        elif step.kind == schema.STEP_INDEX:
            if not isinstance(current, list):
                raise ConfigError(f"Path '{path.display}' addresses an index on a non-array value.")
            _check_index(path, step, len(current), insert=False)
            current = current[step.index]
        else:
            raise ConfigError(f"Path '{path.display}' is an array operation and is not a readable target.")
    return current


def _check_index(path: schema.Path, step: schema.Step, length: int, insert: bool) -> None:
    """
    @brief Validate one array index against the current array length.
    @details Read, replace, and delete require `0 <= Idx < length`; insertion
             requires `0 <= Idx <= length`. Diagnostics name the path, the
             rejected index, the valid range, and the append option.
    @param path {schema.Path} Owning path used in diagnostics.
    @param step {schema.Step} Index or insertion step to validate.
    @param length {int} Current array length.
    @param insert {bool} When `True`, validate insertion bounds.
    @return {None}
    @throws {ConfigError} When the index is out of range.
    @satisfies DES-134
    """
    limit = length if insert else length - 1
    if 0 <= step.index <= limit:
        return
    if insert:
        raise ConfigError(f"Index {step.index} in path '{path.display}' is out of range; valid insert range is 0..{length}.")
    array_path = ":".join(path.tokens[:-1])
    if length == 0:
        raise ConfigError(f"Index {step.index} in path '{path.display}' is out of range; the array is empty; use '--set {array_path}:+ <value>' to add an item.")
    raise ConfigError(f"Index {step.index} in path '{path.display}' is out of range; valid range is 0..{length - 1}; use ':append' to add an item.")
