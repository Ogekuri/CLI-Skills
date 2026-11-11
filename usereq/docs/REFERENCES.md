# Files Structure
```
.
└── src
    ├── cli_skills
    │   ├── __init__.py
    │   ├── __main__.py
    │   ├── catalog.py
    │   ├── configops.py
    │   ├── configview.py
    │   ├── core.py
    │   ├── installer.py
    │   ├── render.py
    │   ├── schema.py
    │   ├── settings.py
    │   ├── show.py
    │   └── targets.py
    └── resources
        └── __init__.py
```

# __init__.py | Python | 13L | 0 symbols | 1 imports | 7 comments
> Path: `src/cli_skills/__init__.py`

## Imports
```
from .core import main  # noqa: F401
```


---

# __main__.py | Python | 11L | 0 symbols | 2 imports | 5 comments
> Path: `src/cli_skills/__main__.py`

## Imports
```
from .core import main
import sys
```


---

# catalog.py | Python | 167L | 10 symbols | 4 imports | 13 comments
> Path: `src/cli_skills/catalog.py`
- @brief Generate the skills manifest for `src/resources`.
- @details Deterministic generator for `src/resources/manifest.json`. Recursively
scans `src/resources/skills` for `SKILL.md` files, extracts frontmatter
`name` and `description`, and emits entries sorted by relative path.
Validates every skill directory against the canonical support layout
before accepting its metadata. Single maintenance path guaranteeing
each manifest description equals its source frontmatter `description`
string (exact match).
- @satisfies DES-021 DES-022 DES-023 DES-024 DES-067 DES-068 DES-069 DES-070 DES-071 DES-072 DES-073

## Imports
```
from __future__ import annotations
import importlib.resources as ires
import json
from pathlib import Path
```

## Definitions

- var `RESOURCES_ROOT = Path(str(ires.files("cli_skills.resources")))` (L22)
- @brief Bundled resources root resolved through the `cli_skills.resources` package.
- @details Setuptools maps `src/resources` to the `cli_skills/resources` distribution path, so the wheel installs no top-level `resources` package.
- @satisfies DES-020 DES-157
- var `MANIFEST_PATH = RESOURCES_ROOT / "manifest.json"` (L23)
- var `SKILL_SUPPORT_DIRECTORIES = ("scripts", "references", "assets", "images")` (L26)
- @brief Canonical skill support subdirectory names allowed at the skill root.
- @details Any other root directory or non-`SKILL.md` root file violates DES-067.
- var `REFERENCE_SUPPORT_DIRECTORIES = ("images",)` (L29)
- @brief Canonical nested subdirectory names allowed directly under `references`.
- @details Any other nested directory under `references` violates DES-069 and DES-070.
### class `class SkillLayoutError(ValueError)` : ValueError (L32-41)
- @brief Signal a bundled skill layout that violates the canonical support layout.
- @details Raised by `validate_skill_layout` when a skill root contains an entry outside the canonical support subdirectories or when `references` contains a non-canonical subdirectory.
- @satisfies DES-073

### fn `def validate_skill_layout(skill_dir: Path) -> None` (L42-70)
- @brief Validate a bundled skill directory against the canonical support layout.
- @details Accepts `SKILL.md` plus the canonical support subdirectories at the skill root; accepts only `images` as a nested directory directly under `references`. Non-canonical root files and directories are rejected. Complexity O(E) where E is the number of root entries plus direct `references` entries.
- @param skill_dir {Path} Packaged skill directory containing `SKILL.md`.
- @return {None}
- @throws {SkillLayoutError} When a root entry or a nested `references` directory violates DES-067 through DES-072.
- @satisfies DES-067 DES-068 DES-069 DES-070 DES-071 DES-072 DES-073
- @pre `skill_dir` MUST be an existing directory.
- @post The directory layout is canonical or an exception is raised.

### fn `def _parse_frontmatter(text: str) -> dict[str, str]` `priv` (L71-103)
- @brief Parse `name` and `description` from a YAML frontmatter block.
- @details Reads key/value lines up to the closing `---` delimiter, strips surrounding YAML quotes from scalar values, and returns only the `name` and `description` keys when present.
- @param text {str} Raw file text (UTF-8).
- @return {Dict[str, str]} Frontmatter `name`/`description` mapping; empty when the block or keys are absent.
- @pre `text` must be a non-empty string.

### fn `def _discover_skills(root: Path) -> list[Path]` `priv` (L104-116)
- @brief Discover `SKILL.md` files under `root/skills`.
- @details Recursively collects every file named `SKILL.md`, sorted by path.
- @param root {Path} Resources root directory.
- @return {List[Path]} Sorted `SKILL.md` file paths.

### fn `def build_catalog(` (L117-118)

### fn `def write_catalog(` (L148-150)
- @brief Build the skills catalog dictionary.
- @details Validates each skill directory layout, then scans the skills
directory, extracts frontmatter metadata, and emits entries
sorted by relative path. Entries missing `name` or `description`
are omitted.
- @param resources_root {Path} Resources root directory to scan.
- @return {Dict[str, List[Dict[str, str]]]} Catalog with a `skills` list;
each entry contains `file`, `name`, `description`.
- @throws {SkillLayoutError} When a discovered skill directory violates the
canonical support layout.
- @satisfies DES-021 DES-022 DES-023 DES-024 DES-067 DES-068 DES-069 DES-070 DES-071 DES-072 DES-073

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`RESOURCES_ROOT`|var|pub|22||
|`MANIFEST_PATH`|var|pub|23||
|`SKILL_SUPPORT_DIRECTORIES`|var|pub|26||
|`REFERENCE_SUPPORT_DIRECTORIES`|var|pub|29||
|`SkillLayoutError`|class|pub|32-41|class SkillLayoutError(ValueError)|
|`validate_skill_layout`|fn|pub|42-70|def validate_skill_layout(skill_dir: Path) -> None|
|`_parse_frontmatter`|fn|priv|71-103|def _parse_frontmatter(text: str) -> dict[str, str]|
|`_discover_skills`|fn|priv|104-116|def _discover_skills(root: Path) -> list[Path]|
|`build_catalog`|fn|pub|117-118|def build_catalog(|
|`write_catalog`|fn|pub|148-150|def write_catalog(|


---

# configops.py | Python | 308L | 13 symbols | 6 imports | 14 comments
> Path: `src/cli_skills/configops.py`
- @brief Validated, atomic configuration reads and mutations over the canonical schema.
- @details Every configuration command bootstraps the global configuration file
from schema defaults when it is missing, resolves canonical paths
through `schema.parse_path`, validates the whole resulting
configuration with `schema.validate_config`, and persists it through
the atomic writer in `settings.save_config`. Reads tolerate malformed
content; mutations fail without writing when the stored configuration
or the requested operation violates the schema.
- @satisfies DES-104 DES-109 DES-111 DES-112 DES-113 DES-114 DES-134 DES-135

## Imports
```
from __future__ import annotations
import copy
import json
from pathlib import Path
from typing import Any
from . import schema, settings
```

## Definitions

### class `class ConfigError(RuntimeError)` : RuntimeError (L24-32)
- @brief Signal a configuration read, resolution, or persistence failure.
- @details Converted by the CLI layer into a stderr diagnostic and exit status 1. No configuration mutation has occurred when raised.
- @satisfies DES-109 DES-114 DES-117

### fn `def ensure_initialized(home: Path | None = None) -> Path` (L33-51)
- @brief Create the configuration directory and file from schema defaults.
- @details Existing files are never overwritten, so a valid configuration survives every configuration command.
- @param home {Path | None} Optional home-directory override.
- @return {Path} Existing or newly initialized configuration file path.
- @throws {OSError} When directory creation or initialization writing fails.
- @satisfies DES-111

### fn `def read_config(home: Path | None = None) -> dict[str, Any]` (L52-65)
- @brief Read the configuration with normalized defaults for display commands.
- @details Bootstraps a missing file, then delegates to the tolerant loader so `--print`, `--info`, and `--get` never fail on foreign content.
- @param home {Path | None} Optional home-directory override.
- @return {dict[str, Any]} Normalized configuration object.
- @throws {OSError} When the configuration cannot be initialized.
- @satisfies DES-111 DES-115 DES-132

### fn `def read_raw(home: Path | None = None) -> bytes` (L66-78)
- @brief Read the unmodified on-disk configuration bytes.
- @details Bootstraps a missing file from schema defaults, then returns the stored bytes without parsing, reformatting, or tree decoration.
- @param home {Path | None} Optional home-directory override.
- @return {bytes} Raw configuration file content.
- @throws {OSError} When initialization or reading fails.
- @satisfies DES-111 DES-116

### fn `def read_strict(home: Path | None = None) -> dict[str, Any]` (L79-99)
- @brief Read and strictly validate the configuration before a mutation.
- @details Bootstraps a missing file, decodes the stored JSON, and rejects malformed payloads, unknown keys, and invalid values.
- @param home {Path | None} Optional home-directory override.
- @return {dict[str, Any]} Schema-valid configuration object.
- @throws {ConfigError} When the file is unreadable, undecodable, or schema-invalid.
- @satisfies DES-112 DES-114

### fn `def get_value(config: dict[str, Any], path: schema.Path) -> Any` (L100-113)
- @brief Read the value addressed by a resolved path.
- @details Rejects array operations, unknown keys, and out-of-range indices before returning the value. Complexity O(S) over path steps.
- @param config {dict[str, Any]} Configuration object.
- @param path {schema.Path} Resolved canonical path.
- @return {Any} Addressed JSON value.
- @throws {ConfigError} For array operations or missing/out-of-range targets.
- @satisfies DES-109 DES-110 DES-115 DES-134

### fn `def apply_set(config: dict[str, Any], path: schema.Path, text: str) -> dict[str, Any]` (L114-156)
- @brief Apply one `--set` operation and return a new configuration object.
- @details Parses the argument into the schema type of the addressed node, replaces, appends, or inserts exactly one value, then validates the whole result. The input object is never mutated.
- @param config {dict[str, Any]} Current schema-valid configuration.
- @param path {schema.Path} Resolved canonical path.
- @param text {str} Raw command-line value.
- @return {dict[str, Any]} New validated configuration object.
- @throws {schema.SchemaError} When the value violates the schema.
- @throws {ConfigError} When the path cannot be navigated or an index is out of range.
- @satisfies DES-110 DES-112 DES-129 DES-134 DES-135

### fn `def apply_unset(config: dict[str, Any], path: schema.Path) -> dict[str, Any]` (L157-191)
- @brief Apply one `--unset` operation and return a new configuration object.
- @details Array indices delete exactly one element and compact later indices; resettable values restore the declared schema default. Values without a schema default are rejected. The input object is never mutated.
- @param config {dict[str, Any]} Current schema-valid configuration.
- @param path {schema.Path} Resolved canonical path.
- @return {dict[str, Any]} New validated configuration object.
- @throws {ConfigError} For array operations, missing targets, out-of-range indices, and values without a declared default.
- @satisfies DES-114 DES-128 DES-134 DES-135

### fn `def set_path(path_text: str, value_text: str, home: Path | None = None) -> schema.Path` (L192-216)
- @brief Resolve one `--set` path, validate the result, and persist atomically.
- @details Reads the configuration strictly, applies the operation in memory, and writes only after full schema validation succeeds.
- @param path_text {str} Canonical colon-separated path.
- @param value_text {str} Raw command-line value.
- @param home {Path | None} Optional home-directory override.
- @return {schema.Path} Resolved path that was written.
- @throws {ConfigError} When resolution, validation, or persistence fails.
- @satisfies DES-111 DES-112 DES-113 DES-114

### fn `def unset_path(path_text: str, home: Path | None = None) -> schema.Path` (L217-240)
- @brief Resolve one `--unset` path, validate the result, and persist atomically.
- @details Reads the configuration strictly, applies the reset or deletion in memory, and writes only after full schema validation succeeds.
- @param path_text {str} Canonical colon-separated path.
- @param home {Path | None} Optional home-directory override.
- @return {schema.Path} Resolved path that was written.
- @throws {ConfigError} When resolution, validation, or persistence fails.
- @satisfies DES-111 DES-113 DES-114 DES-128

### fn `def _parse(path_text: str) -> schema.Path` `priv` (L241-256)
- @brief Resolve a canonical path and normalize schema errors.
- @details Keeps the public operation API uniform: every resolution failure surfaces as `ConfigError` instead of a raw `SchemaError`.
- @param path_text {str} Canonical colon-separated path.
- @return {schema.Path} Resolved path.
- @throws {ConfigError} When the path is empty or schema-invalid.
- @satisfies DES-109 DES-117

### fn `def _navigate(config: dict[str, Any], path: schema.Path, steps: tuple[schema.Step, ...]) -> Any` `priv` (L257-285)
- @brief Walk resolved path steps over the configuration object.
- @details Token steps index mappings; index steps index arrays with bounds validation; append and insert steps are rejected as unreadable.
- @param config {dict[str, Any]} Configuration object.
- @param path {schema.Path} Owning path used in diagnostics.
- @param steps {tuple[schema.Step, ...]} Steps to consume.
- @return {Any} Value or container reached by the steps.
- @throws {ConfigError} For missing keys, non-container values, operations, and out-of-range indices.
- @satisfies DES-109 DES-110 DES-134

### fn `def _check_index(path: schema.Path, step: schema.Step, length: int, insert: bool) -> None` `priv` (L286-309)
- @brief Validate one array index against the current array length.
- @details Read, replace, and delete require `0 <= Idx < length`; insertion requires `0 <= Idx <= length`. Diagnostics name the path, the rejected index, the valid range, and the append option.
- @param path {schema.Path} Owning path used in diagnostics.
- @param step {schema.Step} Index or insertion step to validate.
- @param length {int} Current array length.
- @param insert {bool} When `True`, validate insertion bounds.
- @return {None}
- @throws {ConfigError} When the index is out of range.
- @satisfies DES-134

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`ConfigError`|class|pub|24-32|class ConfigError(RuntimeError)|
|`ensure_initialized`|fn|pub|33-51|def ensure_initialized(home: Path | None = None) -> Path|
|`read_config`|fn|pub|52-65|def read_config(home: Path | None = None) -> dict[str, Any]|
|`read_raw`|fn|pub|66-78|def read_raw(home: Path | None = None) -> bytes|
|`read_strict`|fn|pub|79-99|def read_strict(home: Path | None = None) -> dict[str, Any]|
|`get_value`|fn|pub|100-113|def get_value(config: dict[str, Any], path: schema.Path) ...|
|`apply_set`|fn|pub|114-156|def apply_set(config: dict[str, Any], path: schema.Path, ...|
|`apply_unset`|fn|pub|157-191|def apply_unset(config: dict[str, Any], path: schema.Path...|
|`set_path`|fn|pub|192-216|def set_path(path_text: str, value_text: str, home: Path ...|
|`unset_path`|fn|pub|217-240|def unset_path(path_text: str, home: Path | None = None) ...|
|`_parse`|fn|priv|241-256|def _parse(path_text: str) -> schema.Path|
|`_navigate`|fn|priv|257-285|def _navigate(config: dict[str, Any], path: schema.Path, ...|
|`_check_index`|fn|priv|286-309|def _check_index(path: schema.Path, step: schema.Step, le...|


---

# configview.py | Python | 345L | 19 symbols | 6 imports | 23 comments
> Path: `src/cli_skills/configview.py`
- @brief Build `--print` and `--info` node trees from the canonical schema.
- @details Both commands render the same real configuration nodes through
`render.render_tree`; only heading and detail formatters differ.
Every command example is built from schema example values and
shell-quoted so it stays copy/pasteable and type-valid.
- @satisfies DES-118 DES-119 DES-121 DES-122 DES-123 DES-124 DES-125 DES-126 DES-129 DES-133

## Imports
```
from __future__ import annotations
import json
import shlex
from typing import Any
from . import configops, schema
from .render import Node, render_table, render_tree
```

## Definitions

- var `PRINT_ROOT = f"{schema.ROOT_LABEL} - Current configuration"` (L21)
- @brief Heading of the `--print` display root.
- var `INFO_ROOT = f"{schema.ROOT_LABEL} - Configuration schema reference"` (L23)
- @brief Heading of the `--info` display root.
### fn `def render_print(config: dict[str, Any], path_text: str | None = None) -> str` (L33-47)
- @brief Headers of the allowed-values table rendered by `--info`.
- @brief Render the `--print` tree for the whole configuration or one subtree.
- @details Builds the node tree with `build_print` and renders it with the shared deterministic renderer.
- @param config {dict[str, Any]} Configuration object to display.
- @param path_text {str | None} Optional canonical path limiting the output.
- @return {str} Rendered tree text without trailing newline.
- @throws {schema.SchemaError} When the path cannot be resolved.
- @throws {configops.ConfigError} When the addressed value is unreadable.
- @satisfies DES-118 DES-122 DES-123 DES-127

### fn `def build_print(config: dict[str, Any], path_text: str | None = None) -> Node` (L48-68)
- @brief Build the `--print` node tree for the whole configuration or one subtree.
- @details Without a path the display root carries every section; with a path the requested node becomes the marker-free display root.
- @param config {dict[str, Any]} Configuration object to display.
- @param path_text {str | None} Optional canonical path limiting the output.
- @return {Node} Display root node.
- @throws {schema.SchemaError} When the path cannot be resolved.
- @throws {configops.ConfigError} When the addressed value is unreadable.
- @satisfies DES-118 DES-122 DES-127

### fn `def render_info(path_text: str | None = None) -> str` (L69-81)
- @brief Render the `--info` tree for the whole schema or one subtree.
- @details Uses the same renderer and node topology as `--print`, with schema headings, defaults, and command examples as attached details.
- @param path_text {str | None} Optional canonical path limiting the output.
- @return {str} Rendered tree text without trailing newline.
- @throws {schema.SchemaError} When the path cannot be resolved.
- @satisfies DES-118 DES-125 DES-126 DES-127

### fn `def build_info(path_text: str | None = None) -> Node` (L82-100)
- @brief Build the `--info` node tree for the whole schema or one subtree.
- @details Schema documentation needs no stored configuration, so the tree is derived from the canonical schema alone.
- @param path_text {str | None} Optional canonical path limiting the output.
- @return {Node} Display root node.
- @throws {schema.SchemaError} When the path cannot be resolved.
- @satisfies DES-118 DES-125 DES-126 DES-127

### fn `def _print_section(node: schema.Node, tokens: tuple[str, ...], value: Any) -> Node` `priv` (L101-124)
- @brief Build one `--print` section node with its real children.
- @details The heading carries the exact token, the canonical path badge, and the English description; children keep canonical schema order.
- @param node {schema.Node} Section node to render.
- @param tokens {tuple[str, ...]} Canonical tokens of the section.
- @param value {Any} Stored value of the section mapping.
- @return {Node} Render node for the section.
- @satisfies DES-119 DES-126 DES-127

### fn `def _print_child(node: schema.Node, tokens: tuple[str, ...], value: Any) -> Node` `priv` (L125-138)
- @brief Build one `--print` child node, dispatching sections and parameters.
- @param node {schema.Node} Child schema node.
- @param tokens {tuple[str, ...]} Canonical tokens of the child.
- @param value {Any} Stored value of the child.
- @return {Node} Render node for the child.
- @satisfies DES-122 DES-123 DES-124

### fn `def _print_leaf(node: schema.Node, tokens: tuple[str, ...], value: Any) -> Node` `priv` (L139-165)
- @brief Build one `--print` parameter node with its attached detail lines.
- @details Scalar values render as JSON with a default/custom marker; selections attach a `Sel | Value` table; non-empty arrays attach an `Idx | Value` table; empty arrays attach a complete `--set` hint.
- @param node {schema.Node} Parameter schema node.
- @param tokens {tuple[str, ...]} Canonical tokens of the parameter.
- @param value {Any} Stored value of the parameter.
- @return {Node} Render node for the parameter.
- @satisfies DES-121 DES-122 DES-123 DES-124

### fn `def _print_array(node: schema.Node, label: str, display: str, value: Any) -> Node` `priv` (L166-189)
- @brief Build one `--print` array parameter node.
- @details Non-empty arrays expose the row target and an `Idx | Value` table with contiguous zero-based indices; empty arrays expose a complete, schema-valid `--set` hint without any table.
- @param node {schema.Node} Array schema node.
- @param label {str} Rendered parameter label.
- @param display {str} Canonical path of the array parameter.
- @param value {Any} Stored array value.
- @return {Node} Render node for the array parameter.
- @satisfies DES-121 DES-123

### fn `def _info_section(node: schema.Node, tokens: tuple[str, ...]) -> Node` `priv` (L190-205)
- @brief Build one `--info` section node with its real children.
- @details The section badge precedes the `Reset block` detail; branch metadata is emitted before the real children.
- @param node {schema.Node} Section node to document.
- @param tokens {tuple[str, ...]} Canonical tokens of the section.
- @return {Node} Render node for the section.
- @satisfies DES-125 DES-126

### fn `def _info_child(node: schema.Node, tokens: tuple[str, ...]) -> Node` `priv` (L206-218)
- @brief Build one `--info` child node, dispatching sections and parameters.
- @param node {schema.Node} Child schema node.
- @param tokens {tuple[str, ...]} Canonical tokens of the child.
- @return {Node} Render node for the child.
- @satisfies DES-125

### fn `def _info_leaf(node: schema.Node, tokens: tuple[str, ...]) -> Node` `priv` (L219-261)
- @brief Build one `--info` parameter node with attached schema details.
- @details Emits the declared default with its reset command, full command examples for the addressed value, and the allowed-value table for selections. Required values without defaults never advertise reset.
- @param node {schema.Node} Parameter schema node.
- @param tokens {tuple[str, ...]} Canonical tokens of the parameter.
- @return {Node} Render node for the parameter.
- @satisfies DES-125 DES-128 DES-129

### fn `def _selection_rows(node: schema.Node, current: Any) -> list[tuple[str, str]]` `priv` (L262-277)
- @brief Build `Sel | Value` rows with exactly one active selection row.
- @details Every declared choice produces one row; a stored value outside the declared choices is appended so exactly one row stays active.
- @param node {schema.Node} Selection schema node.
- @param current {Any} Stored value of the selection.
- @return {list[tuple[str, str]]} `(marker, JSON value)` rows.
- @satisfies DES-124

### fn `def _allowed_rows(node: schema.Node, default: Any) -> list[tuple[str, str, str]]` `priv` (L278-294)
- @brief Build `Value | Default | Meaning` rows for one selection node.
- @details The default column reports whether a row equals the declared default; an array item without a default reports `no` everywhere.
- @param node {schema.Node} Selection schema node.
- @param default {Any} Declared default value or `schema.NO_DEFAULT`.
- @return {list[tuple[str, str, str]]} Allowed-value table rows.
- @satisfies DES-125

### fn `def _type_text(node: schema.Node) -> str` `priv` (L295-306)
- @brief Format the bracketed schema type and constraint text of one node.
- @param node {schema.Node} Schema node to describe.
- @return {str} `type: constraints` or just `type`.
- @satisfies DES-125

### fn `def _argument(node: schema.Node, value: Any) -> str` `priv` (L307-322)
- @brief Format one command-line argument as a shell-safe literal.
- @details String and selection values pass as literal text; every other type is JSON-encoded so arrays, objects, numbers, and booleans keep their schema type. Values are single-quoted only when required.
- @param node {schema.Node} Schema node typing the value.
- @param value {Any} Value to render.
- @return {str} Shell-safe argument text.
- @satisfies DES-129

### fn `def _json(value: Any) -> str` `priv` (L323-334)
- @brief Encode one value as a single-line JSON literal.
- @details Newlines and control characters become visible JSON escapes so a value never breaks a structural output line.
- @param value {Any} Value to encode.
- @return {str} JSON text without ASCII escaping.
- @satisfies DES-122 DES-132

### fn `def _require_item(node: schema.Node) -> schema.Node` `priv` (L335-346)
- @brief Return the declared item schema of an array node.
- @param node {schema.Node} Array schema node.
- @return {schema.Node} Declared item schema.
- @throws {schema.SchemaError} When the array declares no item schema.
- @satisfies DES-123

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PRINT_ROOT`|var|pub|21||
|`INFO_ROOT`|var|pub|23||
|`render_print`|fn|pub|33-47|def render_print(config: dict[str, Any], path_text: str |...|
|`build_print`|fn|pub|48-68|def build_print(config: dict[str, Any], path_text: str | ...|
|`render_info`|fn|pub|69-81|def render_info(path_text: str | None = None) -> str|
|`build_info`|fn|pub|82-100|def build_info(path_text: str | None = None) -> Node|
|`_print_section`|fn|priv|101-124|def _print_section(node: schema.Node, tokens: tuple[str, ...|
|`_print_child`|fn|priv|125-138|def _print_child(node: schema.Node, tokens: tuple[str, .....|
|`_print_leaf`|fn|priv|139-165|def _print_leaf(node: schema.Node, tokens: tuple[str, ......|
|`_print_array`|fn|priv|166-189|def _print_array(node: schema.Node, label: str, display: ...|
|`_info_section`|fn|priv|190-205|def _info_section(node: schema.Node, tokens: tuple[str, ....|
|`_info_child`|fn|priv|206-218|def _info_child(node: schema.Node, tokens: tuple[str, ......|
|`_info_leaf`|fn|priv|219-261|def _info_leaf(node: schema.Node, tokens: tuple[str, ...]...|
|`_selection_rows`|fn|priv|262-277|def _selection_rows(node: schema.Node, current: Any) -> l...|
|`_allowed_rows`|fn|priv|278-294|def _allowed_rows(node: schema.Node, default: Any) -> lis...|
|`_type_text`|fn|priv|295-306|def _type_text(node: schema.Node) -> str|
|`_argument`|fn|priv|307-322|def _argument(node: schema.Node, value: Any) -> str|
|`_json`|fn|priv|323-334|def _json(value: Any) -> str|
|`_require_item`|fn|priv|335-346|def _require_item(node: schema.Node) -> schema.Node|


---

# core.py | Python | 635L | 30 symbols | 16 imports | 41 comments
> Path: `src/cli_skills/core.py`

## Imports
```
from __future__ import annotations
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from . import __version__
from . import configops, configview, schema
from .installer import install_enabled, uninstall_enabled
from .settings import load_config, save_config
from .show import build_show
from .targets import TARGETS, resolve_target
```

## Definitions

- var `PYPI_ENDPOINT = "https://pypi.org/pypi/cli-skills/json"` (L24)
- @brief PyPI JSON API endpoint for the newest published version.
- @satisfies DES-042
- var `ENDPOINT = "https://api.github.com/repos/Ogekuri/CLI-Skills/releases/latest"` (L25)
- var `UPGRADE = ["uv", "tool", "install", "cli-skills"]` (L29)
- @brief Standard upgrade argv installing from PyPI without any force option.
- @details Executed for `--upgrade`; runs the standard install/update process.
- @satisfies DES-040 REQ-010
- var `UPGRADE_FORCE = ["uv", "tool", "install", "cli-skills", "--force", "--reinstall", "--refresh"]` (L34)
- @brief Forced-upgrade argv forcing download and complete reinstallation from PyPI.
- @details Executed for `--upgrade --force`; appends the uv tool install
reinstallation options `--force --reinstall --refresh`.
- @satisfies DES-103 REQ-067
- var `UPGRADE_DEVELOP = ["uv", "tool", "install", "cli-skills", "--from", "git+https://github.com/Ogekuri/CLI-Skills.git"]` (L38)
- @brief Upgrade command argv installing the latest tagged GitHub release via git.
- @details Executed for `--upgrade --dev` and `--upgrade --develop`; bypasses PyPI.
- @satisfies DES-081 REQ-063
- var `UPGRADE_DEVELOP_FORCE = ["uv", "tool", "install", "cli-skills", "--force", "--reinstall", "--refresh", "--from", "git+https://github.com/Ogekuri/CLI-Skills.git"]` (L43)
- @brief Forced-upgrade argv forcing download and complete reinstallation from GitHub.
- @details Executed for `--upgrade` combined with `--dev` or `--develop` and
`--force`; appends the reinstallation options before `--from`.
- @satisfies DES-103 REQ-068
- var `UNINSTALL = ["uv", "tool", "uninstall", "cli-skills"]` (L44)
- var `SKILLS_INSTALL = ["cli-skills", "install"]` (L45)
- var `CONFIG_COMMANDS = ("--print", "--info", "--print-raw", "--get", "--set", "--unset")` (L95)
- @brief Configuration commands dispatched through the shared schema.
- @details Order defines the dispatch set only; the help template owns the
documented order.
- @satisfies DES-105 DES-106 DES-130
### fn `def cache_path() -> Path` (L98-101)

### fn `def _human(timestamp: float | None) -> str | None` `priv` (L102-105)

### fn `def _version(value: str) -> tuple[int, int, int]` `priv` (L106-112)

### fn `def _http_json(url: str, accept: str) -> dict` `priv` (L113-130)
- @brief Perform one HTTP GET and parse the JSON response body.
- @details Sends a `cli-skills` User-Agent with the caller-supplied Accept header and enforces the hardcoded 2-second timeout. Network and protocol errors propagate to the caller.
- @param url {str} Absolute HTTP/HTTPS endpoint URL.
- @param accept {str} HTTP Accept header value.
- @return {Dict} Decoded top-level JSON object.
- @throws {OSError} On transport or HTTP errors, including 429 and 503.
- @throws {ValueError} When the response body is not valid JSON.
- @satisfies CTN-006 DES-042 DES-083

### fn `def fetch_pypi_latest() -> str` (L131-148)
- @brief Fetch the newest published version from the PyPI JSON API.
- @details Requests `PYPI_ENDPOINT`, reads `info.version`, and returns it trimmed. Any transport, HTTP, or payload-shape failure raises.
- @return {str} Newest PyPI version string.
- @throws {OSError} On transport or HTTP errors, including 429 and 503.
- @throws {ValueError} When the payload is not valid JSON or omits a non-empty string `info.version`.
- @throws {KeyError} When the payload omits `info.version`.
- @satisfies DES-042 REQ-002 REQ-003 REQ-059

### fn `def fetch_github_latest() -> str` (L149-171)
- @brief Fetch the newest GitHub release version in `x.y.z` form.
- @details Requests `ENDPOINT`, reads `tag_name`, and strips an optional `v` prefix. The returned release is the newest tagged GitHub release regardless of its source branch, matching the `--upgrade --dev` download source.
- @return {str} Newest GitHub release version as `x.y.z`.
- @throws {OSError} On transport or HTTP errors, including 429 and 503.
- @throws {ValueError} When the payload omits or holds an invalid `tag_name`.
- @throws {KeyError} When the payload omits `tag_name`.
- @satisfies DES-083 REQ-061 REQ-062 REQ-063

### fn `def _failure_reason(exc: Exception) -> str` `priv` (L172-195)
- @brief Normalize one release-fetch failure to a concise reason string.
- @details For `HTTPError`, decodes the error body as JSON and surfaces the API `message` field prefixed with `HTTP <code>`; this exposes GitHub rate-limit causes such as `API rate limit exceeded` that arrive with HTTP 404. Body decode failures fall back to `HTTP <code>`; non-HTTP errors return `str(exc)`. Complexity O(B) where B is the error-body byte length.
- @param exc {Exception} Failure raised by `_http_json` or its callers.
- @return {str} Human-readable reason identifying the actual error cause.
- @satisfies REQ-066

### fn `def _report_line(label: str, value: str) -> str` `priv` (L196-210)
- @brief Format one aligned `--ver`/`--version` report line.
- @details Left-justifies `label` to `_REPORT_LABEL_WIDTH` characters and appends `: ` plus the value, so the `:` delimiters and version values align vertically across the three report lines.
- @param label {str} Report label: `Current Installed`, `Latest @ PyPI`, or `Latest @ GitHub`.
- @param value {str} Rendered version or failure value.
- @return {str} Aligned report line without trailing newline.
- @satisfies REQ-006 REQ-060 REQ-061 REQ-070

### fn `def check_version(force: bool = False) -> None` (L211-273)
- @brief Run the cached automatic release check against PyPI.
- @details Skips while the cached idle-time is valid unless `force` is set; otherwise fetches the newest PyPI version via `fetch_pypi_latest`, compares it with `__version__`, prints a bright-green available-versus-installed message when a newer version exists or a bright-red message for a failed or negative check, records last-success timestamps on success only, and writes the cache with a 3600-second (positive) or 86400-second (negative or failed) expiration.
- @param force {bool} Bypass the cached idle-time and perform the request.
- @return {None}
- @note Cache read/write and network failures are reported to stderr and do not raise.
- @satisfies REQ-001 REQ-002 REQ-003 REQ-004 REQ-005 REQ-016 REQ-017 REQ-018 REQ-019 REQ-020 REQ-021 REQ-022 REQ-023 REQ-059 CTN-006 CTN-007 CTN-008 DES-042 DES-043 DES-044 DES-045 DES-046

### fn `def _manage(command: list[str]) -> int` `priv` (L274-284)

### fn `def _post_upgrade_install(home: Path | None = None) -> int` `priv` (L285-309)
- @brief Install bundled resources through `cli-skills install` after a successful upgrade.
- @details Loads the user configuration and, when at least one CLI is enabled, spawns `cli-skills install` as a child process so the freshly upgraded package synchronizes its bundled skills into every enabled CLI. Skips the child process when the enabled configuration is empty. The child reads the upgraded package resources, not the running process ones. The child inherits stdout, so its per-CLI count and installed-name report surfaces as visible `--upgrade` output.
- @param home {Path | None} Optional home-directory override used only for the configuration read; the child process inherits the real environment.
- @return {int} 0 when no CLI is enabled; otherwise the `cli-skills install` exit code (1 on spawn or installation failure).
- @throws {OSError} When reading the configuration file fails.
- @satisfies REQ-043 REQ-044 REQ-046 REQ-058

### fn `def _run_upgrade(command: list[str]) -> int` `priv` (L310-330)
- @brief Execute one upgrade command and chain the post-upgrade install.
- @details Delegates to `_manage` and, on a zero exit code under Linux, chains `_post_upgrade_install` so the freshly upgraded package installs bundled resources into every enabled CLI. Used by the PyPI `--upgrade` form (with or without `--force`) and the GitHub `--upgrade --dev` form (with or without `--force`).
- @param command {list[str]} Upgrade command argv executed on Linux and printed as the manual command on other operating systems.
- @return {int} Upgrade exit code, or the chained `cli-skills install` exit code when the chained install executes.
- @satisfies REQ-010 REQ-011 REQ-012 REQ-043 REQ-044 REQ-045 REQ-046 REQ-063 REQ-067 REQ-068 REQ-069

### fn `def _unsupported(name: str) -> str` `priv` (L331-342)
- @brief Build an unsupported-CLI diagnostic message.
- @details Lists the canonical CLI names accepted by the adapter registry in alphabetical order.
- @param name {str} Unsupported CLI name from the command line.
- @return {str} Human-readable diagnostic message.
- @satisfies REQ-026 DES-092

### fn `def _enable(name: str, home: Path | None = None) -> int` `priv` (L343-368)
- @brief Enable resource installation for one supported CLI.
- @details Resolves the CLI adapter, loads the user configuration, appends the canonical CLI name when absent, and persists the configuration. Re-enabling an enabled CLI leaves configuration unchanged.
- @param name {str} CLI name from the command line.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 on success; 2 for an unsupported CLI.
- @throws {OSError} When saving the configuration file fails.
- @satisfies REQ-024 REQ-026 REQ-027 REQ-028

### fn `def _disable(name: str, home: Path | None = None) -> int` `priv` (L369-395)
- @brief Disable resource installation for one supported CLI.
- @details Resolves the CLI adapter, loads the user configuration, removes the canonical CLI name when present, and persists the configuration. Disabling an already disabled CLI is a successful no-op.
- @param name {str} CLI name from the command line.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 on success; 2 for an unsupported CLI.
- @throws {OSError} When saving the configuration file fails.
- @satisfies REQ-025 REQ-026 REQ-027 REQ-028

### fn `def _install(home: Path | None = None) -> int` `priv` (L396-419)
- @brief Install bundled resources for all enabled CLIs.
- @details Delegates installation to `install_enabled`, prints per-CLI installed skill counts plus the installed skill names, prints an informational message when no CLI is enabled, and reports collected failures.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 when no failure occurs; 1 when any failure occurs.
- @satisfies REQ-029 REQ-030 REQ-031 REQ-032 REQ-057

### fn `def _uninstall(home: Path | None = None) -> int` `priv` (L420-441)
- @brief Remove installed bundled resources for all enabled CLIs.
- @details Delegates uninstallation to `uninstall_enabled`, prints per-CLI removed skill counts, prints an informational message when no CLI is enabled, and reports collected failures.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 when no failure occurs; 1 when any failure occurs.
- @satisfies REQ-047 REQ-054 REQ-055 REQ-056

### fn `def _show(home: Path | None = None) -> int` `priv` (L442-454)
- @brief Print packaged resources, CLI configuration, and installation status.
- @details Delegates report rendering to `build_show` and prints the result.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code 0 after printing the report.
- @throws {OSError} When bundled resources or the configuration cannot be read.
- @satisfies REQ-037 REQ-038 REQ-039 REQ-042

### fn `def _upgrade_command(options: list[str]) -> list[str] | None` `priv` (L455-479)
- @brief Resolve the upgrade argv for the options following `--upgrade`.
- @details Accepts any order of the auxiliary options `--dev`, `--develop`, and `--force`; returns `None` for unknown options, duplicate options, and the redundant `--dev` plus `--develop` combination. `--force` selects the `--force --reinstall --refresh` reinstallation argv; `--dev` or `--develop` selects the GitHub `--from` argv. Complexity O(n) where n is the option count.
- @param options {list[str]} Option tokens following `--upgrade`; empty for the plain `--upgrade` form.
- @return {list[str]} Matching upgrade argv; `None` when the options are invalid.
- @satisfies DES-040 DES-081 DES-103 REQ-010 REQ-063 REQ-067 REQ-068

### fn `def _configure(args: list[str], home: Path | None = None) -> int` `priv` (L480-542)
- @brief Execute one configuration display or mutation command.
- @details Dispatches `--print`, `--info`, `--print-raw`, `--get`, `--set`, and `--unset` against the canonical schema. Valid output goes to stdout; every diagnostic goes to stderr with exit status 1 and no partial success output. `--print-raw` writes the stored bytes unchanged and never applies tree formatting.
- @param args {list[str]} Command token followed by its canonical path and value.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 on success; 1 on any configuration failure.
- @satisfies DES-105 DES-106 DES-111 DES-115 DES-116 DES-117 DES-130

### fn `def main(argv: list[str] | None = None) -> int` (L543-636)
- @brief Run the automatic release check and dispatch one CLI command.
- @details Executes `check_version` before argument parsing (forced by `--ver` or `--version`), then routes to help, version, management, enable/disable, install, uninstall, show, or configuration handlers. Configuration commands dispatch through `_configure` against the canonical schema. The `--upgrade` branch, for any accepted `--dev`/`--develop`/`--force` combination, chains `cli-skills install` after a successful Linux upgrade when the enabled configuration is non-empty and returns the chained exit code. The `--ver` and `--version` branch prints the installed, PyPI, and GitHub versions on the aligned `Current Installed`, `Latest @ PyPI`, and `Latest @ GitHub` lines built by `_report_line`, printing `unavailable (<reason>)` and `unknown (<reason>)` values when the PyPI or GitHub request fails.
- @param argv {list[str] | None} Command-line arguments; defaults to `sys.argv[1:]`.
- @return {int} Process exit code: 0 on success; 1 on upgrade or install failure; 2 on usage errors.
- @satisfies REQ-006 REQ-007 REQ-008 REQ-009 REQ-010 REQ-011 REQ-012 REQ-013 REQ-014 REQ-015 REQ-024 REQ-025 REQ-026 REQ-029 REQ-030 REQ-031 REQ-032 REQ-037 REQ-042 REQ-043 REQ-044 REQ-045 REQ-046 REQ-047 REQ-054 REQ-055 REQ-056 REQ-057 REQ-058 REQ-059 REQ-060 REQ-061 REQ-062 REQ-063 REQ-064 REQ-065 REQ-066 REQ-067 REQ-068 REQ-069 REQ-070 REQ-071 DES-089 DES-103 DES-105 DES-106 DES-130

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PYPI_ENDPOINT`|var|pub|24||
|`ENDPOINT`|var|pub|25||
|`UPGRADE`|var|pub|29||
|`UPGRADE_FORCE`|var|pub|34||
|`UPGRADE_DEVELOP`|var|pub|38||
|`UPGRADE_DEVELOP_FORCE`|var|pub|43||
|`UNINSTALL`|var|pub|44||
|`SKILLS_INSTALL`|var|pub|45||
|`CONFIG_COMMANDS`|var|pub|95||
|`cache_path`|fn|pub|98-101|def cache_path() -> Path|
|`_human`|fn|priv|102-105|def _human(timestamp: float | None) -> str | None|
|`_version`|fn|priv|106-112|def _version(value: str) -> tuple[int, int, int]|
|`_http_json`|fn|priv|113-130|def _http_json(url: str, accept: str) -> dict|
|`fetch_pypi_latest`|fn|pub|131-148|def fetch_pypi_latest() -> str|
|`fetch_github_latest`|fn|pub|149-171|def fetch_github_latest() -> str|
|`_failure_reason`|fn|priv|172-195|def _failure_reason(exc: Exception) -> str|
|`_report_line`|fn|priv|196-210|def _report_line(label: str, value: str) -> str|
|`check_version`|fn|pub|211-273|def check_version(force: bool = False) -> None|
|`_manage`|fn|priv|274-284|def _manage(command: list[str]) -> int|
|`_post_upgrade_install`|fn|priv|285-309|def _post_upgrade_install(home: Path | None = None) -> int|
|`_run_upgrade`|fn|priv|310-330|def _run_upgrade(command: list[str]) -> int|
|`_unsupported`|fn|priv|331-342|def _unsupported(name: str) -> str|
|`_enable`|fn|priv|343-368|def _enable(name: str, home: Path | None = None) -> int|
|`_disable`|fn|priv|369-395|def _disable(name: str, home: Path | None = None) -> int|
|`_install`|fn|priv|396-419|def _install(home: Path | None = None) -> int|
|`_uninstall`|fn|priv|420-441|def _uninstall(home: Path | None = None) -> int|
|`_show`|fn|priv|442-454|def _show(home: Path | None = None) -> int|
|`_upgrade_command`|fn|priv|455-479|def _upgrade_command(options: list[str]) -> list[str] | None|
|`_configure`|fn|priv|480-542|def _configure(args: list[str], home: Path | None = None)...|
|`main`|fn|pub|543-636|def main(argv: list[str] | None = None) -> int|


---

# installer.py | Python | 215L | 8 symbols | 7 imports | 14 comments
> Path: `src/cli_skills/installer.py`
- @brief Orchestrate skill installation for enabled CLI targets.
- @details Builds the bundled resource catalog, resolves manifest skill
directories, invokes the configured CLI adapters, and aggregates
per-CLI outcomes for installation and uninstallation. Rejects a
non-canonical skill support layout through the catalog builder.
- @satisfies PRJ-009 PRJ-011 REQ-029 REQ-030 REQ-032 REQ-035 REQ-047 REQ-048 REQ-051 REQ-052 REQ-053 REQ-056 DES-055 DES-062 DES-064 DES-073

## Imports
```
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from .catalog import RESOURCES_ROOT, SkillLayoutError, build_catalog
from .settings import load_config
from .targets import CliTarget, resolve_target
```

## Definitions

### class `class InstallError(RuntimeError)` : RuntimeError (L22-30)
- @brief Signal a manifest or packaged-resource installation failure.
- @details Raised when a manifest-listed source path is missing, duplicated, or otherwise not installable.
- @satisfies REQ-035

### class `class InstallSummary` `@dataclass(frozen=True)` (L32-47)
- @brief Summarize one CLI installation result.
- @details Carries the canonical CLI name, installed skill count, and sorted installed skill directory names for reporting.
- @satisfies REQ-030 REQ-057

### class `class UninstallSummary` `@dataclass(frozen=True)` (L49-62)
- @brief Summarize one CLI uninstallation result.
- @details Carries the canonical CLI name and processed manifest skill directory count. Missing destinations count as removed.
- @satisfies REQ-054

### fn `def _skill_directories(` `priv` (L63-65)

### fn `def install_target(` (L93-97)
- @brief Resolve manifest skill entries to packaged skill directories.
- @details Validates each entry file path, deduplicates by directory name, and
returns directories sorted by name.
- @param resources_root {Path} Resources root directory.
- @param entries {Iterable[dict[str, str]]} Manifest skill entries.
- @return {list[Path]} Sorted unique skill directories.
- @throws {InstallError} When a manifest-listed skill file or directory is
missing.
- @satisfies DES-055 DES-062 REQ-035

### fn `def install_enabled(` (L121-122)
- @brief Install manifest skills for one CLI target.
- @details Resolves manifest skill directories and delegates skill-tree
synchronization to the adapter.
- @param target {CliTarget} CLI adapter to install.
- @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
- @param resources_root {Path} Resources root directory.
- @param home {Path | None} Optional home-directory override.
- @return {InstallSummary} Installed skill count and names.
- @throws {InstallError} When a manifest-listed source path is missing.
- @throws {OSError} When copying, pruning, or directory creation fails.
- @satisfies REQ-029 REQ-030 REQ-057 DES-055 DES-056 DES-057 DES-062

### fn `def uninstall_target(` (L155-159)
- @brief Install bundled resources for every enabled CLI.
- @details Loads user configuration and builds the resource catalog once.
Processes each enabled CLI independently and collects failures
without stopping remaining CLI processing.
- @param home {Path | None} Optional home-directory override.
- @return {tuple[list[InstallSummary], list[str]]} Installation summaries and
failure diagnostics; both empty when no CLI is enabled.
- @satisfies REQ-029 REQ-030 REQ-031 REQ-032 DES-064 DES-073

### fn `def uninstall_enabled(` (L184-185)
- @brief Remove manifest skills for one CLI target.
- @details Resolves manifest skill directory names and delegates deletion to
the adapter removal method. Missing destinations count as removed.
Destination entries outside manifest skill names are preserved.
- @param target {CliTarget} CLI adapter to clean.
- @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
- @param resources_root {Path} Resources root directory.
- @param home {Path | None} Optional home-directory override.
- @return {UninstallSummary} Removed skill count.
- @throws {InstallError} When a manifest-listed source path is missing.
- @throws {OSError} When destination deletion fails.
- @satisfies REQ-047 REQ-048 REQ-051 REQ-052

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`InstallError`|class|pub|22-30|class InstallError(RuntimeError)|
|`InstallSummary`|class|pub|32-47|class InstallSummary|
|`UninstallSummary`|class|pub|49-62|class UninstallSummary|
|`_skill_directories`|fn|priv|63-65|def _skill_directories(|
|`install_target`|fn|pub|93-97|def install_target(|
|`install_enabled`|fn|pub|121-122|def install_enabled(|
|`uninstall_target`|fn|pub|155-159|def uninstall_target(|
|`uninstall_enabled`|fn|pub|184-185|def uninstall_enabled(|


---

# render.py | Python | 184L | 13 symbols | 4 imports | 14 comments
> Path: `src/cli_skills/render.py`
- @brief Deterministic tree and table rendering primitives shared by every hierarchical command.
- @details The renderer is data driven: a `Node` tree of real configuration nodes
carries headings, attached detail lines, and real children. Structural
prefixes depend only on real siblings, never on column widths, text
length, or detail counts. Attached detail lines reuse the owning node
continuation prefix and never carry structural markers.
- @satisfies DES-118 DES-119 DES-120 DES-127

## Imports
```
from __future__ import annotations
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Sequence
```

## Definitions

- var `BRANCH = "├── "` (L19)
- @brief Structural marker of a node with a later real sibling.
- var `LAST = "└── "` (L21)
- @brief Structural marker of the final real sibling.
- var `INDENT = "    "` (L23)
- @brief Ancestor segment of a level without later real siblings.
- var `CONTINUE = "│   "` (L25)
- @brief Ancestor segment of a level with later real siblings.
- var `ROOT_DETAIL_INDENT = "    "` (L27)
- @brief Detail indentation below an unconnected display root.
### class `class Node` `@dataclass(frozen=True)` (L31-47)
- @brief One real configuration node with attached details and real children.
- @details `details` holds zero or more single-line logical detail strings such as metadata, commands, and rendered table rows. Details never become tree levels and never receive structural markers.
- @param heading {str} Single-line node heading without any tree marker.
- @param details {tuple[str, ...]} Attached single-line detail strings.
- @param children {tuple[Node, ...]} Real child nodes in canonical order.
- @satisfies DES-118 DES-119

### fn `def render_tree(root: Node) -> str` (L48-67)
- @brief Render one configuration tree exactly as required by the prefix algorithm.
- @details Emits the marker-free root heading, its details under a four-space indent, then every real child through `_emit_node`. Complexity O(N) over emitted lines.
- @param root {Node} Unconnected display root.
- @return {str} Rendered tree text without trailing newline.
- @throws {ValueError} When a heading or detail is not a single physical line.
- @satisfies DES-118 DES-119 DES-127

### fn `def display_width(text: str) -> int` (L68-84)
- @brief Measure the terminal display width of one text value.
- @details Combining marks and format characters count as zero width; East Asian wide and fullwidth characters count as two columns.
- @param text {str} Text to measure.
- @return {int} Display width in terminal columns.
- @satisfies DES-120

### fn `def render_table(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> list[str]` (L85-117)
- @brief Render one rectangular box-drawing table with measured column widths.
- @details Column widths derive from the maximum display width of the header and every cell, with one padding space per side. Border characters `┌ ┬ ┐ ├ ┼ ┤ └ ┴ ┘ ─ │` align on shared column boundaries. Cells are never truncated; every row MUST supply exactly one cell per column.
- @param headers {Sequence[str]} Column header labels.
- @param rows {Iterable[Sequence[str]]} Row cell values.
- @return {list[str]} Rendered table lines without prefixes and without newlines.
- @throws {ValueError} When no column is declared, a row has the wrong cell count, or a cell is not a single physical line.
- @satisfies DES-120 DES-121 DES-123

### fn `def _emit_node(node: Node, ancestors: tuple[bool, ...], is_last: bool, lines: list[str]) -> None` `priv` (L118-141)
- @brief Emit one real node, its attached details, and its real children.
- @details The ancestor tuple records only whether each real ancestor has a later real sibling. Detail lines reuse that prefix plus exactly one own continuation segment and never carry tree markers.
- @param node {Node} Real node to emit.
- @param ancestors {tuple[bool, ...]} Later-sibling flags of real ancestors.
- @param is_last {bool} Whether `node` is the final real sibling.
- @param lines {list[str]} Accumulated output lines.
- @return {None}
- @throws {ValueError} When a heading or detail is not a single physical line.
- @satisfies DES-118 DES-119

### fn `def _border(widths: Sequence[int], left: str, middle: str, right: str) -> str` `priv` (L142-154)
- @brief Build one table border line aligned with the measured column widths.
- @param widths {Sequence[int]} Content width of every column.
- @param left {str} Left border character.
- @param middle {str} Column separator character.
- @param right {str} Right border character.
- @return {str} Border line.
- @satisfies DES-120

### fn `def _row(cells: Sequence[str], widths: Sequence[int]) -> list[str]` `priv` (L155-169)
- @brief Build one padded table row.
- @param cells {Sequence[str]} Cell values matching the declared columns.
- @param widths {Sequence[int]} Content width of every column.
- @return {list[str]} Single rendered row line.
- @satisfies DES-120

### fn `def _check_line(text: str, role: str) -> str` `priv` (L170-185)
- @brief Enforce the single-physical-line invariant for one rendered string.
- @details Rejects embedded newlines, carriage returns, tabs, and other control characters so one logical line stays one output line.
- @param text {str} Candidate heading, detail, or cell.
- @param role {str} Human-readable role used in the diagnostic.
- @return {str} The unchanged text when valid.
- @throws {ValueError} When the text contains a control character.
- @satisfies DES-118 DES-119

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`BRANCH`|var|pub|19||
|`LAST`|var|pub|21||
|`INDENT`|var|pub|23||
|`CONTINUE`|var|pub|25||
|`ROOT_DETAIL_INDENT`|var|pub|27||
|`Node`|class|pub|31-47|class Node|
|`render_tree`|fn|pub|48-67|def render_tree(root: Node) -> str|
|`display_width`|fn|pub|68-84|def display_width(text: str) -> int|
|`render_table`|fn|pub|85-117|def render_table(headers: Sequence[str], rows: Iterable[S...|
|`_emit_node`|fn|priv|118-141|def _emit_node(node: Node, ancestors: tuple[bool, ...], i...|
|`_border`|fn|priv|142-154|def _border(widths: Sequence[int], left: str, middle: str...|
|`_row`|fn|priv|155-169|def _row(cells: Sequence[str], widths: Sequence[int]) -> ...|
|`_check_line`|fn|priv|170-185|def _check_line(text: str, role: str) -> str|


---

# schema.py | Python | 476L | 36 symbols | 5 imports | 41 comments
> Path: `src/cli_skills/schema.py`
- @brief Single canonical configuration schema, canonical path grammar, and typed value validation.
- @details The configuration file root object is the `Global` section, so the
file content `{"enabled": [...]}` is addressed as `Global` and its
`enabled` array as `Global:enabled`. Every consumer (path resolution,
typed parsing, validation, defaults, `--print`, `--info`, help text)
derives from the node tree declared here; no parallel parameter list
exists. Value types are `String`, `Integer`, `Float`, `Boolean`,
`Selection`, `Array`, and `Dictionary` (section).
- @satisfies DES-104 DES-107 DES-108 DES-109 DES-110 DES-112 DES-128 DES-134 DES-135

## Imports
```
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any
from .targets import TARGETS
```

## Definitions

- var `ROOT_LABEL = "Application_Configuration"` (L25)
- @brief VIRTUAL display root label of both tree commands.
- @details Never part of a canonical CLI path.
- @satisfies DES-107 DES-118
- var `KIND_SECTION = "section"` (L28)
- @brief Node kind discriminating sections from leaf parameters.
- var `KIND_STRING = "string"` (L29)
- var `KIND_INTEGER = "integer"` (L30)
- var `KIND_FLOAT = "float"` (L31)
- var `KIND_BOOLEAN = "boolean"` (L32)
- var `KIND_SELECTION = "selection"` (L33)
- var `KIND_ARRAY = "array"` (L34)
- var `OP_APPEND = "append"` (L37)
- @brief Canonical array operation tokens reserved for `--set`.
- var `OP_PLUS = "+"` (L38)
- var `OP_INSERT = "insert"` (L39)
- var `STEP_TOKEN = "token"` (L42)
- @brief Path step kinds produced by `parse_path`.
- var `STEP_INDEX = "index"` (L43)
- var `STEP_APPEND = "append"` (L44)
- var `STEP_INSERT = "insert"` (L45)
### class `class _Absent` `priv` (L48-54)
- @brief Sentinel type marking a schema value without a declared default.
- @details Comparison is identity-based; `NO_DEFAULT` is the single instance.

### class `class SchemaError(ValueError)` : ValueError (L59-67)
- @brief Sentinel marking a schema value without a declared default.
- @brief Signal an invalid configuration path or a schema-invalid value.
- @details Raised by `parse_path`, `coerce_value`, and `validate_value`. Consumers convert it into a stderr diagnostic with exit status 1.
- @satisfies DES-109 DES-112 DES-134

### class `class Node` `@dataclass(frozen=True)` (L69-100)
- @brief One schema node representing a section or a leaf parameter.
- @details `children` holds real configuration nodes only; metadata and tables are generated from these fields and are never nodes.
- @param token {str} Exact canonical schema/CLI token.
- @param kind {str} One of the `KIND_*` constants.
- @param description {str} Concise English description of the option.
- @param type_label {str} Displayed schema type such as `Array[Selection]`.
- @param constraints {str} Displayed constraint summary; empty when unconstrained.
- @param default {Any} JSON-ready default or `NO_DEFAULT`.
- @param children {tuple[Node, ...]} Ordered real child nodes of a section.
- @param item {Node | None} Item schema of an array node.
- @param choices {tuple[str, ...]} Allowed values of a selection node.
- @param meanings {tuple[tuple[str, str], ...]} Ordered `(value, meaning)` pairs.
- @param unique {bool} When `True`, array items MUST NOT repeat.
- @satisfies DES-104 DES-108 DES-125

- var `CLI_CONSTRAINTS = "one of: " + ", ".join(SUPPORTED_CLIS)` (L120)
- @brief Displayed constraint of the `enabled` array items.
- var `ENABLED_ITEM = Node(` (L123)
- @brief Schema node of one `Global:enabled` array item.
- var `ENABLED = Node(` (L137)
- @brief Schema node of the `Global:enabled` selection array.
- @details Defaults to the empty list, rejects duplicates, and accepts only
canonical CLI names from the adapter registry.
- @satisfies DES-108 DES-112
- var `GLOBAL = Node(` (L150)
- @brief Schema node of the `Global` section mapped to the configuration file root.
- @satisfies DES-107 DES-126
### fn `def has_default(node: Node) -> bool` (L163-173)
- @brief Ordered top-level sections of the canonical schema.
- @brief Report whether a schema value declares a restorable default.
- @details Exactly one section folds onto the configuration file root object.
- @details Sections always declare defaults because every child declares one.
- @param node {Node} Schema node to inspect.
- @return {bool} `True` when `default_value` yields a restorable value.
- @satisfies DES-128

### fn `def default_value(node: Node) -> Any` (L174-189)
- @brief Build a fresh JSON-ready default value for one schema node.
- @details Array defaults are materialized as new lists so callers never mutate schema state. Sections build a mapping of child defaults.
- @param node {Node} Schema node to materialize.
- @return {Any} JSON-ready default value, or `NO_DEFAULT` when undeclared.
- @satisfies DES-108 DES-128

### fn `def default_config() -> dict[str, Any]` (L190-200)
- @brief Build the on-disk default configuration object.
- @details The file root object equals the `Global` section mapping.
- @return {dict[str, Any]} Fresh default configuration.
- @satisfies DES-111

### fn `def example_value(node: Node) -> Any` (L201-229)
- @brief Build a schema-valid example value for one node.
- @details Used by `--print` empty-collection hints and by every `--info` command example, so published examples stay type-valid.
- @param node {Node} Schema node to exemplify.
- @return {Any} Example value accepted by `validate_value` for `node`.
- @throws {SchemaError} When the node kind has no example rule.
- @satisfies DES-121 DES-129

### class `class Step` `@dataclass(frozen=True)` (L231-244)
- @brief One resolved canonical path step.
- @details `kind` is `STEP_TOKEN`, `STEP_INDEX`, `STEP_APPEND`, or `STEP_INSERT`.
- @param kind {str} Step kind.
- @param token {str} Canonical token text of the step.
- @param index {int} Zero-based index for `STEP_INDEX` and `STEP_INSERT`.

### class `class Path` `@dataclass(frozen=True)` (L246-274)
- @brief Fully resolved canonical configuration path.
- @details `steps` omits the top-level section token because the section maps onto the configuration file root object.
- @param text {str} Original path text supplied by the caller.
- @param tokens {tuple[str, ...]} Canonical display tokens including the section.
- @param steps {tuple[Step, ...]} Data-navigation steps for the root object.
- @param node {Node} Schema node addressed by the path.
- @param section {Node} Top-level section owning the path.
- @satisfies DES-107 DES-109
- fn `def display(self) -> str` (L266-274)
  - @brief Return the canonical colon-separated path text.
  - @return {str} Canonical path built from validated tokens.
  - @satisfies DES-107 DES-129

### fn `def parse_index(text: str, path: str) -> int` (L275-290)
- @brief Parse one non-negative decimal array index.
- @details Accepts ASCII digits only; negative signs and non-decimal text raise `SchemaError`.
- @param text {str} Candidate index token.
- @param path {str} Original path text used in the diagnostic.
- @return {int} Parsed zero-based index.
- @throws {SchemaError} When the token is not a non-negative decimal index.
- @satisfies DES-109 DES-134

### fn `def parse_path(text: str) -> Path` (L291-346)
- @brief Resolve one canonical configuration path against the schema.
- @details Walks the node tree token by token. Sections accept declared child tokens only; arrays accept `append`, `+`, `insert:<Idx>`, or `<Idx>`; leaf parameters terminate the path. Indices are validated for syntax here and for bounds during data navigation. Complexity O(T) where T is the token count.
- @param text {str} Canonical colon-separated path; never includes the virtual root.
- @return {Path} Resolved path with canonical tokens and navigation steps.
- @throws {SchemaError} For empty paths, unknown tokens, malformed indices, and paths continuing past a leaf parameter.
- @satisfies DES-104 DES-107 DES-109 DES-110 DES-134

### fn `def validate_value(node: Node, value: Any, path: str) -> Any` (L347-410)
- @brief Validate one JSON value against a schema node.
- @details Sections reject unknown keys and fill declared defaults; arrays validate every item and reject duplicates when `node.unique`; selections accept declared choices only; scalars enforce their JSON type. Complexity O(N) over nested item count.
- @param node {Node} Schema node defining the accepted shape.
- @param value {Any} Decoded JSON value or literal scalar text.
- @param path {str} Canonical path used in diagnostics.
- @return {Any} Validated value with declared defaults filled in.
- @throws {SchemaError} When the value violates the node contract.
- @satisfies DES-108 DES-109 DES-112

### fn `def validate_config(config: Any) -> dict[str, Any]` (L411-424)
- @brief Validate a complete configuration object against the schema.
- @details Rejects non-object roots, unknown keys, invalid values, and duplicates; declared defaults fill missing keys.
- @param config {Any} Decoded configuration payload.
- @return {dict[str, Any]} Validated configuration object.
- @throws {SchemaError} When the payload violates the schema.
- @satisfies DES-112 DES-113 DES-114

### fn `def coerce_value(node: Node, text: str, path: str) -> Any` (L425-445)
- @brief Parse one command-line value into the schema type of a node.
- @details String and selection arguments are literal text; every other type requires a strict JSON literal so numbers and booleans stay typed.
- @param node {Node} Target schema node.
- @param text {str} Raw command-line argument.
- @param path {str} Canonical path used in diagnostics.
- @return {Any} Parsed and validated value.
- @throws {SchemaError} When JSON decoding or validation fails.
- @satisfies DES-112 DES-114 DES-115 DES-129

### fn `def _find_section(token: str, text: str) -> Node` `priv` (L446-460)
- @brief Resolve a top-level section token.
- @param token {str} First canonical path token.
- @param text {str} Original path text used in the diagnostic.
- @return {Node} Matching section node.
- @throws {SchemaError} When no section declares the token.

### fn `def _find_child(node: Node, token: str, text: str, display: list[str]) -> Node` `priv` (L461-477)
- @brief Resolve one child token inside a section node.
- @param node {Node} Section node being traversed.
- @param token {str} Candidate child token.
- @param text {str} Original path text used in the diagnostic.
- @param display {list[str]} Resolved display tokens before the token.
- @return {Node} Matching child node.
- @throws {SchemaError} When the section declares no such child.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`ROOT_LABEL`|var|pub|25||
|`KIND_SECTION`|var|pub|28||
|`KIND_STRING`|var|pub|29||
|`KIND_INTEGER`|var|pub|30||
|`KIND_FLOAT`|var|pub|31||
|`KIND_BOOLEAN`|var|pub|32||
|`KIND_SELECTION`|var|pub|33||
|`KIND_ARRAY`|var|pub|34||
|`OP_APPEND`|var|pub|37||
|`OP_PLUS`|var|pub|38||
|`OP_INSERT`|var|pub|39||
|`STEP_TOKEN`|var|pub|42||
|`STEP_INDEX`|var|pub|43||
|`STEP_APPEND`|var|pub|44||
|`STEP_INSERT`|var|pub|45||
|`_Absent`|class|priv|48-54|class _Absent|
|`SchemaError`|class|pub|59-67|class SchemaError(ValueError)|
|`Node`|class|pub|69-100|class Node|
|`CLI_CONSTRAINTS`|var|pub|120||
|`ENABLED_ITEM`|var|pub|123||
|`ENABLED`|var|pub|137||
|`GLOBAL`|var|pub|150||
|`has_default`|fn|pub|163-173|def has_default(node: Node) -> bool|
|`default_value`|fn|pub|174-189|def default_value(node: Node) -> Any|
|`default_config`|fn|pub|190-200|def default_config() -> dict[str, Any]|
|`example_value`|fn|pub|201-229|def example_value(node: Node) -> Any|
|`Step`|class|pub|231-244|class Step|
|`Path`|class|pub|246-274|class Path|
|`Path.display`|fn|pub|266-274|def display(self) -> str|
|`parse_index`|fn|pub|275-290|def parse_index(text: str, path: str) -> int|
|`parse_path`|fn|pub|291-346|def parse_path(text: str) -> Path|
|`validate_value`|fn|pub|347-410|def validate_value(node: Node, value: Any, path: str) -> Any|
|`validate_config`|fn|pub|411-424|def validate_config(config: Any) -> dict[str, Any]|
|`coerce_value`|fn|pub|425-445|def coerce_value(node: Node, text: str, path: str) -> Any|
|`_find_section`|fn|priv|446-460|def _find_section(token: str, text: str) -> Node|
|`_find_child`|fn|priv|461-477|def _find_child(node: Node, token: str, text: str, displa...|


---

# settings.py | Python | 135L | 6 symbols | 7 imports | 9 comments
> Path: `src/cli_skills/settings.py`
- @brief Persist enabled CLI targets.
- @details User configuration is a JSON object stored at
`$HOME/.config/cli-skills/config.json` with the schema
`{"enabled": ["<cli>", ...]}`.
Loading tolerates missing, unreadable, or malformed content by
returning normalized defaults.
- @satisfies DES-047 DES-048

## Imports
```
from __future__ import annotations
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any
```

## Definitions

- var `CONFIG_RELATIVE = Path(".config") / "cli-skills" / "config.json"` (L24)
- @brief Configuration path relative to the user home directory.
- @details `$HOME` + `.config/cli-skills/config.json`.
- @satisfies DES-047
### fn `def config_path(home: Path | None = None) -> Path` (L27-38)
- @brief Resolve the user configuration file path.
- @details Joins the effective home directory with `.config/cli-skills/config.json`.
- @param home {Path | None} Optional home-directory override.
- @return {Path} Configuration file path.
- @satisfies DES-047

### fn `def _unique_strings(value: Any) -> list[str]` `priv` (L39-58)
- @brief Filter an arbitrary JSON value into unique non-empty strings.
- @details Preserves first-seen order and drops non-string, empty, and duplicate entries.
- @param value {Any} Candidate JSON value.
- @return {list[str]} Unique strings in first-seen order; empty for non-list input. @complexity O(n) where n is the list length.
- @satisfies DES-048

### fn `def load_config(home: Path | None = None) -> dict[str, Any]` (L59-79)
- @brief Load the user configuration with normalized defaults.
- @details Reads JSON from `config_path`. Missing, unreadable, non-object, or malformed content yields `{"enabled": []}`. Valid `enabled` entries are unique strings.
- @param home {Path | None} Optional home-directory override.
- @return {dict[str, Any]} Normalized configuration object.
- @note Read and decode errors are handled internally and are not raised.
- @satisfies DES-047 DES-048

### fn `def save_config(config: dict[str, Any], home: Path | None = None) -> Path` (L80-115)
- @brief Persist normalized configuration to the user configuration file.
- @details Creates parent directories, serializes with two-space indentation and a trailing newline, writes a unique sibling temporary file, flushes and fsyncs it, preserves the existing file mode, and replaces the target atomically. The parent directory is fsynced when the platform allows it. A failed write removes the temporary file so the previous configuration survives unchanged.
- @param config {dict[str, Any]} Configuration object to persist.
- @param home {Path | None} Optional home-directory override.
- @return {Path} Written configuration file path.
- @throws {OSError} When directory creation, writing, syncing, or replacing fails.
- @satisfies DES-047 DES-048 DES-113 DES-114
- @post The configuration file contains the serialized `config` object.

### fn `def _sync_directory(directory: Path) -> None` `priv` (L116-136)
- @brief Flush a directory entry to disk when the platform supports it.
- @details Opens the directory read-only and fsyncs it; unsupported platforms and permission errors are ignored because the file data is already durable and the replacement is already atomic.
- @param directory {Path} Directory containing the replaced configuration file.
- @return {None}
- @satisfies DES-113

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`CONFIG_RELATIVE`|var|pub|24||
|`config_path`|fn|pub|27-38|def config_path(home: Path | None = None) -> Path|
|`_unique_strings`|fn|priv|39-58|def _unique_strings(value: Any) -> list[str]|
|`load_config`|fn|pub|59-79|def load_config(home: Path | None = None) -> dict[str, Any]|
|`save_config`|fn|pub|80-115|def save_config(config: dict[str, Any], home: Path | None...|
|`_sync_directory`|fn|priv|116-136|def _sync_directory(directory: Path) -> None|


---

# show.py | Python | 289L | 14 symbols | 6 imports | 13 comments
> Path: `src/cli_skills/show.py`
- @brief Render packaged resource inventory, CLI configuration, and installation status.
- @details Builds three deterministic box-drawing-bordered tables: bundled skills from
the manifest, every supported CLI with enabled state and home-relative
skills path, and a per-skill per-enabled-CLI installation status
derived from destination-directory scans.
- @satisfies DES-065 DES-066 REQ-037 REQ-038 REQ-039 REQ-040

## Imports
```
from __future__ import annotations
from pathlib import Path
from typing import Any, Iterable, Sequence
from .catalog import RESOURCES_ROOT, build_catalog
from .settings import load_config
from .targets import TARGETS, resolve_home
```

## Definitions

- var `MAX_CELL_WIDTH = 48` (L21)
- @brief Maximum rendered width of one table cell in characters.
- var `STATUS_OK = "OK"` (L23)
- @brief Status value for a resource whose destination files match the package.
- var `STATUS_MISSING = "MISSING"` (L25)
- @brief Status value for a resource with missing destination directories or files.
- var `STATUS_STALE = "STALE"` (L27)
- @brief Status value for a resource whose destination files differ from the package.
### fn `def _wrap(text: str, width: int) -> list[str]` `priv` (L30-63)
- @brief Wrap one cell value into fixed-width lines on word boundaries.
- @details Collapses whitespace, splits overlong tokens into `width`-sized chunks, and greedily packs words without exceeding `width`.
- @param text {str} Cell value to wrap.
- @param width {int} Maximum line width in characters; MUST be positive.
- @return {list[str]} Rendered lines; `[""]` for an empty value.
- @satisfies DES-066

### fn `def render_table(` (L64-67)

### fn `def border(left: str, middle: str, right: str) -> str` (L90-92)
- @brief Render a box-drawing-bordered grid table with aligned and wrapped cells.
- @details Column widths are the longest cell capped by `max_width`; the
header opens with a `┌─┬┐` border and closes with an `├─┼┤`
separator, rows are emitted between `│` verticals, and the table
ends with a `└─┴┘` border. Multi-line cells are padded to the row
height.
- @param headers {Sequence[str]} Column header labels.
- @param rows {Iterable[Sequence[str]]} Row cell values; short rows are padded.
- @param max_width {int} Maximum column width in characters.
- @return {str} Rendered table text without trailing newline.
- @satisfies DES-066

### fn `def render(cells: Sequence[str]) -> list[str]` (L97-115)

### fn `def _resource_rows(` `priv` (L123-124)

### fn `def _cli_rows(` `priv` (L146-148)
- @brief Build inventory rows from manifest catalog entries.
- @details Emits skills preserving manifest entry order.
- @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
- @return {list[tuple[str, str, str, str]]} `(type, name, file, description)` rows.
- @satisfies REQ-037

### fn `def _files_match(source: Path, destination: Path) -> str` `priv` (L173-191)
- @brief Build CLI configuration rows from the adapter registry.
- @brief Compare one packaged file with its installed destination file.
- @details Reports alphabetical registry order, enabled state, and the
home-relative skills destination.
- @param config {dict[str, object]} Normalized user configuration.
- @param home {Path | None} Optional home-directory override.
- @param source {Path} Packaged file path.
- @param destination {Path} Installed destination file path.
- @return {list[tuple[str, str, str]]} `(cli, enabled, skills path)` rows.
- @return {str} `OK` for identical bytes, `MISSING` for absent destination, `STALE` for differing bytes or unreadable content.
- @satisfies REQ-038 DES-092
- @satisfies REQ-040

### fn `def _skill_status(source: Path, destination: Path) -> str` `priv` (L192-215)
- @brief Compare a packaged skill directory with its installed copy.
- @details Every packaged regular file must exist in the destination with identical bytes.
- @param source {Path} Packaged skill directory.
- @param destination {Path} Installed skill destination directory.
- @return {str} `OK` when all files match; `MISSING` when the package or a destination file is absent; `STALE` on content mismatch.
- @satisfies REQ-040

### fn `def _install_rows(` `priv` (L216-219)

### fn `def build_show(home: Path | None = None) -> str` (L256-290)
- @brief Build per-skill per-enabled-CLI installation status rows.
- @brief Build the complete `show` report text.
- @details Scans adapter destination directories for each manifest skill
and emits rows only for CLIs present in the enabled
configuration.
- @details Renders the packaged-resource inventory, CLI configuration, and installation status tables in this order.
- @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
- @param config {dict[str, object]} Normalized user configuration.
- @param home {Path | None} Optional home-directory override.
- @param home {Path | None} Optional home-directory override for deterministic destination resolution.
- @return {list[tuple[str, str, str, str, str]]} `(type, name, cli, enabled,
installed)` rows.
- @return {str} Report text with three titled tables separated by blank lines.
- @throws {OSError} When the manifest or bundled resources cannot be read.
- @satisfies REQ-039 REQ-040
- @satisfies DES-065 REQ-037 REQ-038 REQ-039 REQ-042

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`MAX_CELL_WIDTH`|var|pub|21||
|`STATUS_OK`|var|pub|23||
|`STATUS_MISSING`|var|pub|25||
|`STATUS_STALE`|var|pub|27||
|`_wrap`|fn|priv|30-63|def _wrap(text: str, width: int) -> list[str]|
|`render_table`|fn|pub|64-67|def render_table(|
|`border`|fn|pub|90-92|def border(left: str, middle: str, right: str) -> str|
|`render`|fn|pub|97-115|def render(cells: Sequence[str]) -> list[str]|
|`_resource_rows`|fn|priv|123-124|def _resource_rows(|
|`_cli_rows`|fn|priv|146-148|def _cli_rows(|
|`_files_match`|fn|priv|173-191|def _files_match(source: Path, destination: Path) -> str|
|`_skill_status`|fn|priv|192-215|def _skill_status(source: Path, destination: Path) -> str|
|`_install_rows`|fn|priv|216-219|def _install_rows(|
|`build_show`|fn|pub|256-290|def build_show(home: Path | None = None) -> str|


---

# targets.py | Python | 293L | 21 symbols | 5 imports | 27 comments
> Path: `src/cli_skills/targets.py`
- @brief Provide per-CLI skill installation adapters.
- @details Defines the `CliTarget` abstraction and one concrete adapter for each
supported CLI: `antigravity`, `claude`, `codex`, `copilot`, `opencode`,
`openclaw`, and `pi`.
Adapters resolve user-level skill destination directories from a home
root and provide deterministic copy algorithms for skills.
Shared copy primitives synchronize packaged trees, overwrite changed
files, and prune destination entries absent from the package.
Removal primitives delete managed skill directories while preserving
unmanaged destination entries.
- @satisfies PRJ-010 PRJ-011 DES-049 DES-050 DES-051 DES-052 DES-053 DES-054 DES-090 DES-091 DES-092 DES-055 DES-056 DES-057 DES-058 DES-063 REQ-048 REQ-051 REQ-052

## Imports
```
from __future__ import annotations
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable
```

## Definitions

### fn `def resolve_home(home: Path | None) -> Path` (L24-36)
- @brief Resolve the user home directory used for destination paths.
- @details Returns the explicit override when provided; otherwise resolves `Path.home()`. Centralizes home resolution for deterministic tests and adapter reuse.
- @param home {Path | None} Optional home-directory override.
- @return {Path} Effective home directory path.
- @satisfies DES-049

### fn `def sync_skill_tree(source: Path, destination: Path) -> None` (L37-69)
- @brief Replace a destination skill directory with packaged contents.
- @details Copies the source tree recursively with overwrite, then removes destination files and directories absent from the source tree. Destination skill files become byte-identical copies of package files. Pruning runs deepest-first to keep directory removal safe.
- @param source {Path} Packaged skill directory containing `SKILL.md`.
- @param destination {Path} Target skill directory named after `source.name`.
- @return {None}
- @throws {OSError} When directory creation, copying, or pruning fails.
- @satisfies DES-055 DES-056 DES-057 DES-063
- @pre `source` MUST be an existing directory.
- @post `destination` contains exactly the source tree paths and contents. @complexity O(S + D) where S is source entries and D is destination entries.

### class `class CliTarget(ABC)` : ABC (L70-132)
- @brief Abstract adapter for a supported CLI installation target.
- @details Subclasses declare the CLI name and resolve the user-level skill destination directory. Base methods implement deterministic skill-tree synchronization and managed skill removal.
- @satisfies DES-049 REQ-048
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L83-90)
  - @brief Resolve the CLI user-level skills destination directory.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} Skills destination directory.
  - @satisfies DES-050 DES-051 DES-052 DES-053 DES-054
- fn `def install_skills(self, sources: Iterable[Path], home: Path | None = None) -> int` (L91-108)
  - @brief Install packaged skill directories into this CLI destination.
  - @details Synchronizes each source directory into `<skills_dir>/<source.name>` using `sync_skill_tree`.
  - @param sources {Iterable[Path]} Packaged skill directories.
  - @param home {Path | None} Optional home-directory override.
  - @return {int} Number of processed skill directories.
  - @throws {OSError} When synchronization fails.
  - @satisfies DES-055 DES-056 DES-057 DES-063
- fn `def remove_skills(self, names: Iterable[str], home: Path | None = None) -> int` (L109-132)
  - @brief Remove managed skill directories from this CLI destination.
  - @details Deletes `<skills_dir>/<name>` recursively for each name. Missing destinations count as removed and do not raise. Destination entries outside `names` are preserved and no directory is created. Complexity O(N) deletions where N is the number of names.
  - @param names {Iterable[str]} Managed skill directory names.
  - @param home {Path | None} Optional home-directory override.
  - @return {int} Number of processed names; missing destinations count as removed.
  - @throws {OSError} When recursive directory deletion fails.
  - @satisfies REQ-048 REQ-051 REQ-052

### class `class PiTarget(CliTarget)` : CliTarget (L133-151)
- @brief Installation adapter for the `pi` coding agent.
- @details Installs skills under `$HOME/.pi/agent/skills`.
- @satisfies DES-050
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L142-151)
  - @brief Installation adapter for the `pi` coding agent.
  - @brief Resolve the pi user-level skills directory.
  - @details Installs skills under `$HOME/.pi/agent/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.pi/agent/skills`.
  - @satisfies DES-050
  - @satisfies DES-050

### class `class OpenClawTarget(CliTarget)` : CliTarget (L152-170)
- @brief Installation adapter for the `openclaw` agent workspace.
- @details Installs skills under `$HOME/.openclaw/workspace/skills`.
- @satisfies DES-051
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L161-170)
  - @brief Installation adapter for the `openclaw` agent workspace.
  - @brief Resolve the openclaw user-level skills directory.
  - @details Installs skills under `$HOME/.openclaw/workspace/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.openclaw/workspace/skills`.
  - @satisfies DES-051
  - @satisfies DES-051

### class `class CodexTarget(CliTarget)` : CliTarget (L171-189)
- @brief Installation adapter for the `codex` CLI.
- @details Installs skills under `$HOME/.codex/skills`.
- @satisfies DES-052
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L180-189)
  - @brief Installation adapter for the `codex` CLI.
  - @brief Resolve the codex user-level skills directory.
  - @details Installs skills under `$HOME/.codex/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.codex/skills`.
  - @satisfies DES-052
  - @satisfies DES-052

### class `class CopilotTarget(CliTarget)` : CliTarget (L190-208)
- @brief Installation adapter for the `copilot` CLI.
- @details Installs skills under `$HOME/.copilot/skills`.
- @satisfies DES-091
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L199-208)
  - @brief Installation adapter for the `copilot` CLI.
  - @brief Resolve the copilot user-level skills directory.
  - @details Installs skills under `$HOME/.copilot/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.copilot/skills`.
  - @satisfies DES-091
  - @satisfies DES-091

### class `class AntigravityTarget(CliTarget)` : CliTarget (L209-227)
- @brief Installation adapter for Google Antigravity.
- @details Installs skills under `$HOME/.gemini/config/skills`.
- @satisfies DES-053
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L218-227)
  - @brief Installation adapter for Google Antigravity.
  - @brief Resolve the antigravity user-level skills directory.
  - @details Installs skills under `$HOME/.gemini/config/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.gemini/config/skills`.
  - @satisfies DES-053
  - @satisfies DES-053

### class `class OpenCodeTarget(CliTarget)` : CliTarget (L228-246)
- @brief Installation adapter for the `opencode` CLI.
- @details Installs skills under `$HOME/.config/opencode/skills`.
- @satisfies DES-090
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L237-246)
  - @brief Installation adapter for the `opencode` CLI.
  - @brief Resolve the opencode user-level skills directory.
  - @details Installs skills under `$HOME/.config/opencode/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.config/opencode/skills`.
  - @satisfies DES-090
  - @satisfies DES-090

### class `class ClaudeTarget(CliTarget)` : CliTarget (L247-265)
- @brief Installation adapter for the `claude` CLI.
- @details Installs skills under `$HOME/.claude/skills`.
- @satisfies DES-054
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L256-265)
  - @brief Installation adapter for the `claude` CLI.
  - @brief Resolve the claude user-level skills directory.
  - @details Installs skills under `$HOME/.claude/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.claude/skills`.
  - @satisfies DES-054
  - @satisfies DES-054

### fn `def resolve_target(name: str) -> CliTarget | None` (L284-294)
- @brief Registry of supported CLI adapters keyed by canonical CLI name.
- @brief Resolve a CLI adapter by canonical name.
- @details Alphabetical key order defines the supported-name listing in
diagnostics and `show` tables.
- @details Trims surrounding whitespace and lowercases the input before a registry lookup.
- @param name {str} CLI name supplied on the command line.
- @return {CliTarget | None} Matching adapter; `None` when unsupported.
- @satisfies DES-049 DES-092
- @satisfies REQ-026

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`resolve_home`|fn|pub|24-36|def resolve_home(home: Path | None) -> Path|
|`sync_skill_tree`|fn|pub|37-69|def sync_skill_tree(source: Path, destination: Path) -> None|
|`CliTarget`|class|pub|70-132|class CliTarget(ABC)|
|`CliTarget.skills_dir`|fn|pub|83-90|def skills_dir(self, home: Path | None = None) -> Path|
|`CliTarget.install_skills`|fn|pub|91-108|def install_skills(self, sources: Iterable[Path], home: P...|
|`CliTarget.remove_skills`|fn|pub|109-132|def remove_skills(self, names: Iterable[str], home: Path ...|
|`PiTarget`|class|pub|133-151|class PiTarget(CliTarget)|
|`PiTarget.skills_dir`|fn|pub|142-151|def skills_dir(self, home: Path | None = None) -> Path|
|`OpenClawTarget`|class|pub|152-170|class OpenClawTarget(CliTarget)|
|`OpenClawTarget.skills_dir`|fn|pub|161-170|def skills_dir(self, home: Path | None = None) -> Path|
|`CodexTarget`|class|pub|171-189|class CodexTarget(CliTarget)|
|`CodexTarget.skills_dir`|fn|pub|180-189|def skills_dir(self, home: Path | None = None) -> Path|
|`CopilotTarget`|class|pub|190-208|class CopilotTarget(CliTarget)|
|`CopilotTarget.skills_dir`|fn|pub|199-208|def skills_dir(self, home: Path | None = None) -> Path|
|`AntigravityTarget`|class|pub|209-227|class AntigravityTarget(CliTarget)|
|`AntigravityTarget.skills_dir`|fn|pub|218-227|def skills_dir(self, home: Path | None = None) -> Path|
|`OpenCodeTarget`|class|pub|228-246|class OpenCodeTarget(CliTarget)|
|`OpenCodeTarget.skills_dir`|fn|pub|237-246|def skills_dir(self, home: Path | None = None) -> Path|
|`ClaudeTarget`|class|pub|247-265|class ClaudeTarget(CliTarget)|
|`ClaudeTarget.skills_dir`|fn|pub|256-265|def skills_dir(self, home: Path | None = None) -> Path|
|`resolve_target`|fn|pub|284-294|def resolve_target(name: str) -> CliTarget | None|


---

# __init__.py | Python | 9L | 0 symbols | 0 imports | 1 comments
> Path: `src/resources/__init__.py`
- @brief Mark `src/resources` as the bundled skills package `cli_skills.resources`.
- @details Provides an importable package for the `src/resources` data tree. Setuptools
maps this directory to `cli_skills/resources` in the `cli-skills` distribution
so downstream LLM agents resolve bundled artifacts via `importlib.resources`
under `cli_skills.resources`.
- @satisfies PRJ-006 PRJ-007 DES-020

