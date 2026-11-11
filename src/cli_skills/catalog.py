"""
@file catalog.py
@brief Generate the skills manifest for `src/resources`.
@details Deterministic generator for `src/resources/manifest.json`. Recursively
         scans `src/resources/skills` for `SKILL.md` files, extracts frontmatter
         `name` and `description`, and emits entries sorted by relative path.
         Validates every skill directory against the canonical support layout
         before accepting its metadata. Single maintenance path guaranteeing
         each manifest description equals its source frontmatter `description`
         string (exact match).
@satisfies DES-021 DES-022 DES-023 DES-024 DES-067 DES-068 DES-069 DES-070 DES-071 DES-072 DES-073
"""

from __future__ import annotations

import importlib.resources as ires
import json
from pathlib import Path

## @brief Bundled resources root resolved through the `cli_skills.resources` package.
## @details Setuptools maps `src/resources` to the `cli_skills/resources` distribution path, so the wheel installs no top-level `resources` package. @satisfies DES-020 DES-157
RESOURCES_ROOT = Path(str(ires.files("cli_skills.resources")))
MANIFEST_PATH = RESOURCES_ROOT / "manifest.json"
## @brief Canonical skill support subdirectory names allowed at the skill root.
## @details Any other root directory or non-`SKILL.md` root file violates DES-067.
SKILL_SUPPORT_DIRECTORIES = ("scripts", "references", "assets", "images")
## @brief Canonical nested subdirectory names allowed directly under `references`.
## @details Any other nested directory under `references` violates DES-069 and DES-070.
REFERENCE_SUPPORT_DIRECTORIES = ("images",)


class SkillLayoutError(ValueError):
    """
    @brief Signal a bundled skill layout that violates the canonical support layout.
    @details Raised by `validate_skill_layout` when a skill root contains an
             entry outside the canonical support subdirectories or when
             `references` contains a non-canonical subdirectory.
    @satisfies DES-073
    """


def validate_skill_layout(skill_dir: Path) -> None:
    """
    @brief Validate a bundled skill directory against the canonical support layout.
    @details Accepts `SKILL.md` plus the canonical support subdirectories at the
             skill root; accepts only `images` as a nested directory directly
             under `references`. Non-canonical root files and directories are
             rejected. Complexity O(E) where E is the number of root entries
             plus direct `references` entries.
    @param skill_dir {Path} Packaged skill directory containing `SKILL.md`.
    @return {None}
    @throws {SkillLayoutError} When a root entry or a nested `references`
            directory violates DES-067 through DES-072.
    @satisfies DES-067 DES-068 DES-069 DES-070 DES-071 DES-072 DES-073
    @pre `skill_dir` MUST be an existing directory.
    @post The directory layout is canonical or an exception is raised.
    """
    for entry in sorted(skill_dir.iterdir()):
        if entry.name == "SKILL.md" and entry.is_file():
            continue
        if entry.is_dir() and entry.name in SKILL_SUPPORT_DIRECTORIES:
            continue
        raise SkillLayoutError(f"Invalid skill entry: {entry}")
    references = skill_dir / "references"
    if references.is_dir():
        for entry in sorted(references.iterdir()):
            if entry.is_dir() and entry.name not in REFERENCE_SUPPORT_DIRECTORIES:
                raise SkillLayoutError(f"Invalid references entry: {entry}")


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


def build_catalog(
    resources_root: Path = RESOURCES_ROOT,
) -> dict[str, list[dict[str, str]]]:
    """
    @brief Build the skills catalog dictionary.
    @details Validates each skill directory layout, then scans the skills
             directory, extracts frontmatter metadata, and emits entries
             sorted by relative path. Entries missing `name` or `description`
             are omitted.
    @param resources_root {Path} Resources root directory to scan.
    @return {Dict[str, List[Dict[str, str]]]} Catalog with a `skills` list;
            each entry contains `file`, `name`, `description`.
    @throws {SkillLayoutError} When a discovered skill directory violates the
            canonical support layout.
    @satisfies DES-021 DES-022 DES-023 DES-024 DES-067 DES-068 DES-069 DES-070 DES-071 DES-072 DES-073
    """
    catalog: dict[str, list[dict[str, str]]] = {"skills": []}
    for path in _discover_skills(resources_root):
        validate_skill_layout(path.parent)
        meta = _parse_frontmatter(path.read_text(encoding="utf-8"))
        if "name" in meta and "description" in meta:
            catalog["skills"].append(
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
