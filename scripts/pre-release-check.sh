#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# pre-release-check.sh - Pre-release verification gate for cli-skills.
# AUTHORS: Ogekuri

#/**
# * @brief Resolve absolute path of executing script.
# * @details Uses `readlink -f "$0"` to canonicalize all symlinks and relative
# *          components before directory extraction.
# */
FULL_PATH=$(readlink -f "$0")

#/**
# * @brief Extract script directory and project base directory.
# * @details SCRIPT_PATH is the directory containing this script; BASE_DIR is
# *          its parent, expected to be the repository root.
# */
SCRIPT_PATH=$(dirname "$FULL_PATH")
BASE_DIR=$(dirname "$SCRIPT_PATH")

#/**
# * @brief Resolve and validate the project root against the launcher path.
# * @details Uses `git -C rev-parse --show-toplevel`; aborts with an explicit
# *          error when root detection fails or when the launcher base
# *          directory differs from the git root, preventing mixed-root
# *          execution with a non-deterministic environment.
# */
PROJECT_ROOT=$(git -C "${BASE_DIR}" rev-parse --show-toplevel 2>/dev/null)
if [ -z "${PROJECT_ROOT}" ]; then
    echo "ERROR: Unable to determine project root from launcher path."
    exit 1
fi
if [ "${PROJECT_ROOT}" != "${BASE_DIR}" ]; then
    echo "ERROR: Launcher base directory mismatch with git root."
    echo "git root: ${PROJECT_ROOT}"
    echo "launcher base: ${BASE_DIR}"
    exit 1
fi

set -euo pipefail
cd "${BASE_DIR}"

#/**
# * @brief Temporary build output directory removed by the EXIT cleanup trap.
# * @details Distributions are built outside the repository tree so no build
# *          artifact can remain behind on success, failure, or interruption.
# * @satisfies DES-084 DES-087
# */
BUILD_DIR=$(mktemp -d)

#/**
# * @brief Remove every artifact created by the pre-release checks.
# * @details Deletes the temporary build directory, any in-repository build
# *          output directory (`build/`, `dist/`), setuptools egg-info
# *          directories under `src/`, and Python bytecode cache directories
# *          under `src/` and `tests/`. Registered on EXIT so cleanup runs on
# *          success, failure, and interruption. The uv-managed `.venv` is
# *          environment infrastructure and is preserved.
# * @satisfies DES-087
# */
cleanup() {
    rm -rf "${BUILD_DIR}"
    rm -rf "${BASE_DIR}/build"
    rm -rf "${BASE_DIR}/dist"
    rm -rf "${BASE_DIR}"/src/*.egg-info
    find "${BASE_DIR}/src" "${BASE_DIR}/tests" -type d -name "__pycache__" -prune -exec rm -rf "{}" + 2>/dev/null || true
}
trap cleanup EXIT

#/**
# * @brief Build source and wheel distributions with the release command.
# * @details Executes `uv run --frozen --with build python -m build`, the same
# *          command used by the release workflow, writing outputs to the
# *          temporary build directory. Failure aborts the gate.
# * @satisfies DES-084 PRJ-014
# */
echo "==> [1/3] Building distributions (sdist and wheel) into ${BUILD_DIR}"
uv run --frozen --with build python -m build --outdir "${BUILD_DIR}"

#/**
# * @brief Validate distribution metadata for PyPI compliance.
# * @details Executes `twine check` on every built artifact; metadata defects
# *          that would block a PyPI upload fail the gate.
# * @satisfies DES-085 PRJ-014
# */
echo "==> [2/3] Checking distribution metadata with twine"
uv run --frozen --with twine python -m twine check "${BUILD_DIR}"/*

#/**
# * @brief Run the project-defined unit-test suite.
# * @details Executes `uv run python -m unittest discover -s tests`, the
# *          standard test command documented for the repository. Any test
# *          failure fails the gate through `set -e`.
# * @satisfies DES-086 PRJ-014
# */
echo "==> [3/3] Running unit tests"
uv run python -m unittest discover -s tests

echo "==> Pre-release checks passed."
