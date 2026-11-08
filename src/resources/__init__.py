"""
@file __init__.py
@brief Mark `resources` as the bundled skills distribution package.
@details Provides an importable namespace for the `src/resources` data tree so
         setuptools packages it with the `cli-skills` distribution and downstream
         LLM agents can resolve bundled artifacts via `importlib.resources`.
@satisfies PRJ-006 PRJ-007 DES-020
"""
