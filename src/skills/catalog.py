"""
@file catalog.py
@brief Generate the skills and prompts manifest for `src/resources`.
@details Deterministic generator for `src/resources/manifest.json`. Recursively
         scans `src/resources/skills` for `SKILL.md` files and
         `src/resources/prompts` for frontmatter files, extracts frontmatter
         `name` and `description`, and emits entries sorted by relative path.
         Single maintenance path guaranteeing each manifest description equals
         its source frontmatter `description` string (exact match).
@satisfies DES-021 DES-022 DES-023 DES-024
"""

from __future__ import annotations

import importlib.resources as ires
import json
from pathlib import Path

RESOURCES_ROOT = Path(str(ires.files("resources")))
MANIFEST_PATH = RESOURCES_ROOT / "manifest.json"


def _parse_frontmatter(text: str) -> dict[str, str]:
    """
    @brief Parse `name` and `description` from a YAML frontmatter block.
    @details Reads key/value lines up to the closing `---` delimiter, strips
             surrounding YAML quotes from scalar values, and returns only the
             `name` and `description` keys when present.
    @param text {str} Raw file text (UTF-8).
    @return {Dict[str, str]} Frontmatter `name`/`description` mapping; empty
            when the block or keys are absent.
    @pre `text` must be a non-empty string.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = 1
    while end < len(lines) and lines[end].strip() != "---":
        end += 1
    if end >= len(lines):
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key in ("name", "description"):
            fields[key] = value
    return fields


def _discover_skills(root: Path) -> list[Path]:
    """
    @brief Discover `SKILL.md` files under `root/skills`.
    @details Recursively collects every file named `SKILL.md`, sorted by path.
    @param root {Path} Resources root directory.
    @return {List[Path]} Sorted `SKILL.md` file paths.
    """
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return []
    return sorted(p for p in skills_dir.rglob("SKILL.md") if p.is_file())


def _discover_prompts(root: Path) -> list[Path]:
    """
    @brief Discover candidate prompt files under `root/prompts`.
    @details Recursively collects every regular file, sorted by path.
             Frontmatter filtering is applied by `build_catalog`.
    @param root {Path} Resources root directory.
    @return {List[Path]} Sorted candidate prompt file paths.
    """
    prompts_dir = root / "prompts"
    if not prompts_dir.is_dir():
        return []
    return sorted(p for p in prompts_dir.rglob("*") if p.is_file())


def build_catalog(
    resources_root: Path = RESOURCES_ROOT,
) -> dict[str, list[dict[str, str]]]:
    """
    @brief Build the skills and prompts catalog dictionary.
    @details Scans skills and prompts directories, extracts frontmatter
             metadata, and emits entries sorted by relative path. Entries
             missing `name` or `description` are omitted.
    @param resources_root {Path} Resources root directory to scan.
    @return {Dict[str, List[Dict[str, str]]]} Catalog with `skills` and
            `prompts` lists; each entry contains `file`, `name`, `description`.
    @satisfies DES-021 DES-022 DES-023 DES-024
    """
    catalog: dict[str, list[dict[str, str]]] = {"skills": [], "prompts": []}
    for path in _discover_skills(resources_root):
        meta = _parse_frontmatter(path.read_text(encoding="utf-8"))
        if "name" in meta and "description" in meta:
            catalog["skills"].append(
                {
                    "file": path.relative_to(resources_root).as_posix(),
                    "name": meta["name"],
                    "description": meta["description"],
                }
            )
    for path in _discover_prompts(resources_root):
        meta = _parse_frontmatter(path.read_text(encoding="utf-8"))
        if "name" in meta and "description" in meta:
            catalog["prompts"].append(
                {
                    "file": path.relative_to(resources_root).as_posix(),
                    "name": meta["name"],
                    "description": meta["description"],
                }
            )
    return catalog


def write_catalog(
    resources_root: Path = RESOURCES_ROOT,
    dest: Path = MANIFEST_PATH,
) -> Path:
    """
    @brief Write the catalog to the JSON manifest file.
    @details Serializes `build_catalog` output deterministically with UTF-8
             encoding, two-space indent, no ASCII escaping, and trailing newline.
    @param resources_root {Path} Resources root directory to scan.
    @param dest {Path} Destination JSON manifest file path.
    @return {Path} The written manifest file path.
    @satisfies DES-021
    """
    catalog = build_catalog(resources_root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return dest
