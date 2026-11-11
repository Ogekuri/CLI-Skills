"""
@file schema.py
@brief Single canonical configuration schema, canonical path grammar, and typed value validation.
@details The configuration file root object is the `Global` section, so the
         file content `{"enabled": [...]}` is addressed as `Global` and its
         `enabled` array as `Global:enabled`. Every consumer (path resolution,
         typed parsing, validation, defaults, `--print`, `--info`, help text)
         derives from the node tree declared here; no parallel parameter list
         exists. Value types are `String`, `Integer`, `Float`, `Boolean`,
         `Selection`, `Array`, and `Dictionary` (section).
@satisfies DES-104 DES-107 DES-108 DES-109 DES-110 DES-112 DES-128 DES-134 DES-135
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .targets import TARGETS

## @brief VIRTUAL display root label of both tree commands.
# @details Never part of a canonical CLI path.
# @satisfies DES-107 DES-118
ROOT_LABEL = "Application_Configuration"

## @brief Node kind discriminating sections from leaf parameters.
KIND_SECTION = "section"
KIND_STRING = "string"
KIND_INTEGER = "integer"
KIND_FLOAT = "float"
KIND_BOOLEAN = "boolean"
KIND_SELECTION = "selection"
KIND_ARRAY = "array"

## @brief Canonical array operation tokens reserved for `--set`.
OP_APPEND = "append"
OP_PLUS = "+"
OP_INSERT = "insert"

## @brief Path step kinds produced by `parse_path`.
STEP_TOKEN = "token"
STEP_INDEX = "index"
STEP_APPEND = "append"
STEP_INSERT = "insert"


class _Absent:
    """
    @brief Sentinel type marking a schema value without a declared default.
    @details Comparison is identity-based; `NO_DEFAULT` is the single instance.
    """


## @brief Sentinel marking a schema value without a declared default.
NO_DEFAULT: Any = _Absent()


class SchemaError(ValueError):
    """
    @brief Signal an invalid configuration path or a schema-invalid value.
    @details Raised by `parse_path`, `coerce_value`, and `validate_value`.
    Consumers convert it into a stderr diagnostic with exit status 1.
    @satisfies DES-109 DES-112 DES-134
    """


@dataclass(frozen=True)
class Node:
    """
    @brief One schema node representing a section or a leaf parameter.
    @details `children` holds real configuration nodes only; metadata and
             tables are generated from these fields and are never nodes.
    @param token {str} Exact canonical schema/CLI token.
    @param kind {str} One of the `KIND_*` constants.
    @param description {str} Concise English description of the option.
    @param type_label {str} Displayed schema type such as `Array[Selection]`.
    @param constraints {str} Displayed constraint summary; empty when unconstrained.
    @param default {Any} JSON-ready default or `NO_DEFAULT`.
    @param children {tuple[Node, ...]} Ordered real child nodes of a section.
    @param item {Node | None} Item schema of an array node.
    @param choices {tuple[str, ...]} Allowed values of a selection node.
    @param meanings {tuple[tuple[str, str], ...]} Ordered `(value, meaning)` pairs.
    @param unique {bool} When `True`, array items MUST NOT repeat.
    @satisfies DES-104 DES-108 DES-125
    """

    token: str
    kind: str
    description: str
    type_label: str
    constraints: str = ""
    default: Any = NO_DEFAULT
    children: tuple[Node, ...] = ()
    item: Node | None = None
    choices: tuple[str, ...] = ()
    meanings: tuple[tuple[str, str], ...] = ()
    unique: bool = False


## @brief Canonical supported CLI names in alphabetical order.
# @details Derived from the adapter registry so listings never diverge.
# @satisfies DES-092 DES-108
SUPPORTED_CLIS: tuple[str, ...] = tuple(TARGETS)

## @brief English meaning of every canonical CLI name.
# @details Key order matches `SUPPORTED_CLIS`; `--info` renders one row per name.
# @satisfies DES-125 DES-133
CLI_MEANINGS: dict[str, str] = {
    "antigravity": "Google Antigravity",
    "claude": "Claude Code CLI",
    "codex": "OpenAI Codex CLI",
    "copilot": "GitHub Copilot CLI",
    "openclaw": "OpenClaw agent workspace",
    "opencode": "OpenCode CLI",
    "pi": "Pi coding agent",
}

## @brief Displayed constraint of the `enabled` array items.
CLI_CONSTRAINTS = "one of: " + ", ".join(SUPPORTED_CLIS)

## @brief Schema node of one `Global:enabled` array item.
ENABLED_ITEM = Node(
    token="item",
    kind=KIND_SELECTION,
    description="Supported CLI name",
    type_label="Selection",
    constraints=CLI_CONSTRAINTS,
    choices=SUPPORTED_CLIS,
    meanings=tuple(CLI_MEANINGS.items()),
)

## @brief Schema node of the `Global:enabled` selection array.
# @details Defaults to the empty list, rejects duplicates, and accepts only
#          canonical CLI names from the adapter registry.
# @satisfies DES-108 DES-112
ENABLED = Node(
    token="enabled",
    kind=KIND_ARRAY,
    description="Enabled CLI targets for skill installation",
    type_label="Array[Selection]",
    constraints="unique supported CLI names",
    default=(),
    item=ENABLED_ITEM,
    unique=True,
)

## @brief Schema node of the `Global` section mapped to the configuration file root.
# @satisfies DES-107 DES-126
GLOBAL = Node(
    token="Global",
    kind=KIND_SECTION,
    description="Global user configuration file",
    type_label="Dictionary",
    children=(ENABLED,),
)

## @brief Ordered top-level sections of the canonical schema.
# @details Exactly one section folds onto the configuration file root object.
SECTIONS: tuple[Node, ...] = (GLOBAL,)


def has_default(node: Node) -> bool:
    """
    @brief Report whether a schema value declares a restorable default.
    @details Sections always declare defaults because every child declares one.
    @param node {Node} Schema node to inspect.
    @return {bool} `True` when `default_value` yields a restorable value.
    @satisfies DES-128
    """
    return node.kind == KIND_SECTION or node.default is not NO_DEFAULT


def default_value(node: Node) -> Any:
    """
    @brief Build a fresh JSON-ready default value for one schema node.
    @details Array defaults are materialized as new lists so callers never
             mutate schema state. Sections build a mapping of child defaults.
    @param node {Node} Schema node to materialize.
    @return {Any} JSON-ready default value, or `NO_DEFAULT` when undeclared.
    @satisfies DES-108 DES-128
    """
    if node.kind == KIND_SECTION:
        return {child.token: default_value(child) for child in node.children}
    if isinstance(node.default, tuple):
        return list(node.default)
    return node.default


def default_config() -> dict[str, Any]:
    """
    @brief Build the on-disk default configuration object.
    @details The file root object equals the `Global` section mapping.
    @return {dict[str, Any]} Fresh default configuration.
    @satisfies DES-111
    """
    value = default_value(GLOBAL)
    return dict(value)


def example_value(node: Node) -> Any:
    """
    @brief Build a schema-valid example value for one node.
    @details Used by `--print` empty-collection hints and by every `--info`
             command example, so published examples stay type-valid.
    @param node {Node} Schema node to exemplify.
    @return {Any} Example value accepted by `validate_value` for `node`.
    @throws {SchemaError} When the node kind has no example rule.
    @satisfies DES-121 DES-129
    """
    if node.kind == KIND_SECTION:
        return default_value(node)
    if node.kind == KIND_SELECTION:
        return node.choices[0]
    if node.kind == KIND_STRING:
        return "value"
    if node.kind == KIND_INTEGER:
        return 1
    if node.kind == KIND_FLOAT:
        return 1.0
    if node.kind == KIND_BOOLEAN:
        return True
    if node.kind == KIND_ARRAY:
        if node.item is None:
            raise SchemaError(f"Schema array '{node.token}' declares no item type.")
        return [example_value(node.item)]
    raise SchemaError(f"Schema node '{node.token}' declares the unsupported kind '{node.kind}'.")


@dataclass(frozen=True)
class Step:
    """
    @brief One resolved canonical path step.
    @details `kind` is `STEP_TOKEN`, `STEP_INDEX`, `STEP_APPEND`, or `STEP_INSERT`.
    @param kind {str} Step kind.
    @param token {str} Canonical token text of the step.
    @param index {int} Zero-based index for `STEP_INDEX` and `STEP_INSERT`.
    """

    kind: str
    token: str
    index: int = -1


@dataclass(frozen=True)
class Path:
    """
    @brief Fully resolved canonical configuration path.
    @details `steps` omits the top-level section token because the section maps
             onto the configuration file root object.
    @param text {str} Original path text supplied by the caller.
    @param tokens {tuple[str, ...]} Canonical display tokens including the section.
    @param steps {tuple[Step, ...]} Data-navigation steps for the root object.
    @param node {Node} Schema node addressed by the path.
    @param section {Node} Top-level section owning the path.
    @satisfies DES-107 DES-109
    """

    text: str
    tokens: tuple[str, ...]
    steps: tuple[Step, ...]
    node: Node
    section: Node

    @property
    def display(self) -> str:
        """
        @brief Return the canonical colon-separated path text.
        @return {str} Canonical path built from validated tokens.
        @satisfies DES-107 DES-129
        """
        return ":".join(self.tokens)


def parse_index(text: str, path: str) -> int:
    """
    @brief Parse one non-negative decimal array index.
    @details Accepts ASCII digits only; negative signs and non-decimal text
             raise `SchemaError`.
    @param text {str} Candidate index token.
    @param path {str} Original path text used in the diagnostic.
    @return {int} Parsed zero-based index.
    @throws {SchemaError} When the token is not a non-negative decimal index.
    @satisfies DES-109 DES-134
    """
    if not (text.isascii() and text.isdigit()):
        raise SchemaError(f"Invalid index '{text}' in path '{path}': expected a non-negative decimal index.")
    return int(text)


def parse_path(text: str) -> Path:
    """
    @brief Resolve one canonical configuration path against the schema.
    @details Walks the node tree token by token. Sections accept declared child
             tokens only; arrays accept `append`, `+`, `insert:<Idx>`, or
             `<Idx>`; leaf parameters terminate the path. Indices are validated
             for syntax here and for bounds during data navigation. Complexity
             O(T) where T is the token count.
    @param text {str} Canonical colon-separated path; never includes the virtual root.
    @return {Path} Resolved path with canonical tokens and navigation steps.
    @throws {SchemaError} For empty paths, unknown tokens, malformed indices,
             and paths continuing past a leaf parameter.
    @satisfies DES-104 DES-107 DES-109 DES-110 DES-134
    """
    if not isinstance(text, str) or not text:
        raise SchemaError("Configuration path MUST NOT be empty.")
    tokens = tuple(text.split(":"))
    section = _find_section(tokens[0], text)
    steps: list[Step] = []
    display: list[str] = [section.token]
    node = section
    position = 1
    while position < len(tokens):
        token = tokens[position]
        if node.kind == KIND_SECTION:
            child = _find_child(node, token, text, display)
            steps.append(Step(STEP_TOKEN, token))
            display.append(token)
            node = child
            position += 1
            continue
        if node.kind != KIND_ARRAY or node.item is None:
            raise SchemaError(f"Invalid path '{text}': '{':'.join(display)}' is a leaf parameter and accepts no further token.")
        if token in (OP_APPEND, OP_PLUS):
            steps.append(Step(STEP_APPEND, token))
            display.append(token)
            node = node.item
            position += 1
            continue
        if token == OP_INSERT:
            if position + 1 >= len(tokens):
                raise SchemaError(f"Invalid path '{text}': '{token}' requires a following insertion index.")
            index = parse_index(tokens[position + 1], text)
            steps.append(Step(STEP_INSERT, tokens[position + 1], index))
            display.extend((token, tokens[position + 1]))
            node = node.item
            position += 2
            continue
        index = parse_index(token, text)
        steps.append(Step(STEP_INDEX, token, index))
        display.append(token)
        node = node.item
        position += 1
    return Path(text=text, tokens=tuple(display), steps=tuple(steps), node=node, section=section)


def validate_value(node: Node, value: Any, path: str) -> Any:
    """
    @brief Validate one JSON value against a schema node.
    @details Sections reject unknown keys and fill declared defaults; arrays
             validate every item and reject duplicates when `node.unique`;
             selections accept declared choices only; scalars enforce their
             JSON type. Complexity O(N) over nested item count.
    @param node {Node} Schema node defining the accepted shape.
    @param value {Any} Decoded JSON value or literal scalar text.
    @param path {str} Canonical path used in diagnostics.
    @return {Any} Validated value with declared defaults filled in.
    @throws {SchemaError} When the value violates the node contract.
    @satisfies DES-108 DES-109 DES-112
    """
    if node.kind == KIND_SECTION:
        if not isinstance(value, dict):
            raise SchemaError(f"Path '{path}' requires a JSON object.")
        known = {child.token for child in node.children}
        for key in value:
            if key not in known:
                raise SchemaError(f"Path '{path}' rejects unknown key '{key}'.")
        result: dict[str, Any] = {}
        for child in node.children:
            child_path = f"{path}:{child.token}"
            if child.token in value:
                result[child.token] = validate_value(child, value[child.token], child_path)
            elif has_default(child):
                result[child.token] = default_value(child)
            else:
                raise SchemaError(f"Path '{path}' requires the key '{child.token}'.")
        return result
    if node.kind == KIND_ARRAY:
        if not isinstance(value, list):
            raise SchemaError(f"Path '{path}' requires a JSON array.")
        if node.item is None:
            raise SchemaError(f"Schema array '{path}' declares no item type.")
        items = [validate_value(node.item, entry, f"{path}:{index}") for index, entry in enumerate(value)]
        if node.unique and len({repr(entry) for entry in items}) != len(items):
            raise SchemaError(f"Path '{path}' rejects duplicate items.")
        return items
    if node.kind == KIND_SELECTION:
        if not isinstance(value, str) or value not in node.choices:
            allowed = ", ".join(node.choices)
            raise SchemaError(f"Path '{path}' requires one of: {allowed}; received {value!r}.")
        return value
    if node.kind == KIND_STRING:
        if not isinstance(value, str):
            raise SchemaError(f"Path '{path}' requires a JSON string.")
        return value
    if node.kind == KIND_INTEGER:
        if not isinstance(value, int) or isinstance(value, bool):
            raise SchemaError(f"Path '{path}' requires a JSON integer.")
        return value
    if node.kind == KIND_FLOAT:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise SchemaError(f"Path '{path}' requires a JSON number.")
        return value
    if node.kind == KIND_BOOLEAN:
        if not isinstance(value, bool):
            raise SchemaError(f"Path '{path}' requires a JSON boolean.")
        return value
    raise SchemaError(f"Schema path '{path}' declares the unsupported kind '{node.kind}'.")


def validate_config(config: Any) -> dict[str, Any]:
    """
    @brief Validate a complete configuration object against the schema.
    @details Rejects non-object roots, unknown keys, invalid values, and
             duplicates; declared defaults fill missing keys.
    @param config {Any} Decoded configuration payload.
    @return {dict[str, Any]} Validated configuration object.
    @throws {SchemaError} When the payload violates the schema.
    @satisfies DES-112 DES-113 DES-114
    """
    value = validate_value(GLOBAL, config, GLOBAL.token)
    return dict(value)


def coerce_value(node: Node, text: str, path: str) -> Any:
    """
    @brief Parse one command-line value into the schema type of a node.
    @details String and selection arguments are literal text; every other type
             requires a strict JSON literal so numbers and booleans stay typed.
    @param node {Node} Target schema node.
    @param text {str} Raw command-line argument.
    @param path {str} Canonical path used in diagnostics.
    @return {Any} Parsed and validated value.
    @throws {SchemaError} When JSON decoding or validation fails.
    @satisfies DES-112 DES-114 DES-115 DES-129
    """
    if node.kind in (KIND_STRING, KIND_SELECTION):
        return validate_value(node, text, path)
    try:
        payload = json.loads(text)
    except ValueError as exc:
        raise SchemaError(f"Path '{path}' requires a JSON {node.type_label} value: {exc}.") from exc
    return validate_value(node, payload, path)


def _find_section(token: str, text: str) -> Node:
    """
    @brief Resolve a top-level section token.
    @param token {str} First canonical path token.
    @param text {str} Original path text used in the diagnostic.
    @return {Node} Matching section node.
    @throws {SchemaError} When no section declares the token.
    """
    for section in SECTIONS:
        if section.token == token:
            return section
    known = ", ".join(section.token for section in SECTIONS)
    raise SchemaError(f"Unknown configuration section '{token}' in path '{text}'. Known sections: {known}.")


def _find_child(node: Node, token: str, text: str, display: list[str]) -> Node:
    """
    @brief Resolve one child token inside a section node.
    @param node {Node} Section node being traversed.
    @param token {str} Candidate child token.
    @param text {str} Original path text used in the diagnostic.
    @param display {list[str]} Resolved display tokens before the token.
    @return {Node} Matching child node.
    @throws {SchemaError} When the section declares no such child.
    """
    for child in node.children:
        if child.token == token:
            return child
    known = ", ".join(child.token for child in node.children)
    parent = ":".join(display)
    raise SchemaError(f"Unknown configuration key '{token}' in '{parent}' of path '{text}'. Known keys: {known}.")
