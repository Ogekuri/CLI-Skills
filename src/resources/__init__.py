"""
@file __init__.py
@brief Mark `src/resources` as the bundled skills package `cli_skills.resources`.
@details Provides an importable package for the `src/resources` data tree. Setuptools
         maps this directory to `cli_skills/resources` in the `cli-skills` distribution
         so downstream LLM agents resolve bundled artifacts via `importlib.resources`
         under `cli_skills.resources`.
@satisfies PRJ-006 PRJ-007 DES-020
"""
