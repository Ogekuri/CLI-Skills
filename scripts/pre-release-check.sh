#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# VERSION: 0.10.2
# Authoritative release-readiness checks for cli-skills.
#
#/**
# * @file pre-release-check.sh
# * @brief Verify release readiness and remove artifacts created by this run.
# * @details Validates repository structure, locked dependencies, shell and
# *          Python syntax, the complete unittest suite, release distributions,
# *          and Twine metadata. An EXIT trap preserves the original failure,
# *          removes only outputs absent before invocation, and compares Git
# *          status and diffs with their initial snapshots.
# * @satisfies PRJ-014 DES-084 DES-085 DES-086 DES-087 DES-137 DES-143 DES-144
# *            DES-145 DES-147 DES-148 DES-149 DES-150
# */

set -Eeuo pipefail

#/** @brief Original script path used to resolve the repository root. */
SCRIPT_LOCATION=${BASH_SOURCE[0]}
#/** @brief Directory containing the invoked pre-release script. */
SCRIPT_DIRECTORY=${SCRIPT_LOCATION%/*}
if [[ "$SCRIPT_DIRECTORY" == "$SCRIPT_LOCATION" ]]; then
    SCRIPT_DIRECTORY=.
fi
cd -- "$SCRIPT_DIRECTORY/.."
#/** @brief Absolute repository root selected from the script location. */
PROJECT_ROOT=$PWD

#/** @brief Active validation stage reported by diagnostics and final summary. */
CURRENT_PHASE=initialization
#/** @brief First failed validation stage, retained through cleanup. */
FAILED_PHASE=
#/** @brief Temporary directory for state snapshots and the isolated uv environment. */
CHECK_DIRECTORY=
#/** @brief Whether the pre-release process created its temporary directory. */
CHECK_DIRECTORY_OWNED=0
#/** @brief Whether this run invoked the release build script. */
BUILD_ATTEMPTED=0
#/** @brief Whether dist existed before this check. */
DIST_PREEXISTED=0
#/** @brief Whether cleanup targets were verified absent before checks began. */
CLEANUP_TARGETS_SAFE=0
#/** @brief Exit status retained from the verification workflow. */
ORIGINAL_STATUS=0

#/**
# * @brief Emit a fatal diagnostic and terminate the check.
# * @details Writes one stage-specific error to stderr and exits nonzero so the
# *          EXIT trap performs cleanup without changing the failure result.
# * @param message {string} Failure detail without a required trailing newline.
# * @return {never} Does not return.
# * @satisfies PRJ-014 DES-139 DES-144 DES-145
# */
die() {
    printf 'ERROR: [%s] %s\n' "$CURRENT_PHASE" "$1" >&2
    FAILED_PHASE=$CURRENT_PHASE
    exit 1
}

#/**
# * @brief Remove only build and test outputs created during this run.
# * @details Uses the build-script manifest to delete verified generated release
# *          files, removes source and test bytecode/intermediate directories
# *          only after preflight proved they were absent, removes a newly
# *          created empty dist directory, then verifies Git status and both
# *          staged and unstaged diffs against pre-run snapshots.
# * @return {int} Zero when cleanup and integrity verification succeed.
# * @throws {SystemExit} When an artifact cannot be safely removed or state differs.
# * @satisfies DES-087 DES-139 DES-144 DES-145
# */
cleanup() {
    local status=0

    if (( BUILD_ATTEMPTED == 1 )); then
        if ! "$PROJECT_ROOT/scripts/build.sh" --clean-generated; then
            printf 'ERROR: Cleanup could not remove verified release outputs.\n' >&2
            status=1
        fi
    fi

    if (( CLEANUP_TARGETS_SAFE == 1 )); then
        if [[ -e "$PROJECT_ROOT/build" ]] &&
            ! rm -rf -- "$PROJECT_ROOT/build"; then
            printf 'ERROR: Cleanup could not remove generated build/.\n' >&2
            status=1
        fi
        if ! find "$PROJECT_ROOT/src" "$PROJECT_ROOT/tests" -type d \
            \( -name '*.egg-info' -o -name '__pycache__' \) -prune \
            -exec rm -rf -- {} +; then
            printf 'ERROR: Cleanup could not remove generated Python intermediates.\n' >&2
            status=1
        fi
    fi

    if (( DIST_PREEXISTED == 0 )) && [[ -d "$PROJECT_ROOT/dist" ]] &&
        ! rmdir -- "$PROJECT_ROOT/dist"; then
        printf 'ERROR: Cleanup left unexpected content in newly created dist/.\n' >&2
        status=1
    fi

    if (( CHECK_DIRECTORY_OWNED == 1 )) && [[ -d "$CHECK_DIRECTORY" ]]; then
        if ! git -C "$PROJECT_ROOT" status --porcelain --untracked-files=all \
            > "$CHECK_DIRECTORY/status.after"; then
            printf 'ERROR: Cleanup could not verify final Git status.\n' >&2
            status=1
        fi
        if ! cmp -s "$CHECK_DIRECTORY/status.before" "$CHECK_DIRECTORY/status.after"; then
            printf 'ERROR: Git status changed during pre-release verification.\n' >&2
            status=1
        fi
        if ! git -C "$PROJECT_ROOT" diff --binary \
            > "$CHECK_DIRECTORY/unstaged.after"; then
            printf 'ERROR: Cleanup could not verify the unstaged diff.\n' >&2
            status=1
        fi
        if ! cmp -s "$CHECK_DIRECTORY/unstaged.before" "$CHECK_DIRECTORY/unstaged.after"; then
            printf 'ERROR: Tracked working-tree content changed during verification.\n' >&2
            status=1
        fi
        if ! git -C "$PROJECT_ROOT" diff --cached --binary \
            > "$CHECK_DIRECTORY/staged.after"; then
            printf 'ERROR: Cleanup could not verify the staged diff.\n' >&2
            status=1
        fi
        if ! cmp -s "$CHECK_DIRECTORY/staged.before" "$CHECK_DIRECTORY/staged.after"; then
            printf 'ERROR: Git index content changed during verification.\n' >&2
            status=1
        fi
    fi

    if (( CHECK_DIRECTORY_OWNED == 1 )) && [[ -d "$CHECK_DIRECTORY" ]]; then
        if ! rm -rf -- "$CHECK_DIRECTORY"; then
            printf 'ERROR: Cleanup could not remove verification snapshots.\n' >&2
            status=1
        fi
    fi
    if (( CHECK_DIRECTORY_OWNED == 1 )) && [[ -e "$CHECK_DIRECTORY" ]]; then
        printf 'ERROR: Temporary check output remains: %s\n' "$CHECK_DIRECTORY" >&2
        status=1
    fi
    return "$status"
}

#/**
# * @brief Preserve verification status while enforcing successful cleanup.
# * @details EXIT captures the original status, disables recursive traps,
# *          performs cleanup, and returns nonzero when checks or cleanup fail.
# *          A passing summary is emitted only after all cleanup checks pass.
# * @return {never} Exits with the original verification or cleanup status.
# * @satisfies DES-087 DES-139 DES-144 DES-145
# */
finish() {
    ORIGINAL_STATUS=$?
    local cleanup_status=0
    trap - EXIT ERR INT TERM HUP
    if ! cleanup; then
        cleanup_status=1
    fi
    if (( ORIGINAL_STATUS == 0 && cleanup_status != 0 )); then
        ORIGINAL_STATUS=1
        FAILED_PHASE=cleanup
    fi
    if (( ORIGINAL_STATUS == 0 )); then
        printf 'Pre-release checks: PASS; cleanup: PASS.\n'
    else
        if [[ -z "$FAILED_PHASE" ]]; then
            FAILED_PHASE=$CURRENT_PHASE
        fi
        printf 'Pre-release checks: FAIL at %s (status %d).\n' \
            "$FAILED_PHASE" "$ORIGINAL_STATUS" >&2
    fi
    exit "$ORIGINAL_STATUS"
}

#/**
# * @brief Route command and signal failures through the cleanup handler.
# * @details Stores the first failed stage and exits with the original command
# *          status; the EXIT handler remains responsible for cleanup.
# * @param status {int} Original nonzero command status.
# * @param detail {string} Failed command text or signal identifier.
# * @return {never} Exits with the original failure status.
# * @satisfies DES-139 DES-144
# */
on_error() {
    local status=$1
    local detail=$2
    FAILED_PHASE=$CURRENT_PHASE
    printf 'ERROR: [%s] %s (status %d).\n' "$CURRENT_PHASE" "$detail" "$status" >&2
    exit "$status"
}

trap finish EXIT
trap 'on_error "$?" "$BASH_COMMAND"' ERR
trap 'on_error 130 INT' INT
trap 'on_error 143 TERM' TERM
trap 'on_error 129 HUP' HUP

(( $# == 0 )) || die 'Usage: scripts/pre-release-check.sh'
[[ -f "$PROJECT_ROOT/pyproject.toml" && -f "$PROJECT_ROOT/uv.lock" &&
    -f "$PROJECT_ROOT/.github/workflows/release-pypi.yml" &&
    -d "$PROJECT_ROOT/src/cli_skills" && -d "$PROJECT_ROOT/tests" ]] ||
    die 'Required project metadata, workflow, source, or test directory is missing.'
command -v git >/dev/null 2>&1 || die 'Required tool is unavailable: git.'
command -v uv >/dev/null 2>&1 || die 'Required tool is unavailable: uv.'
command -v bash >/dev/null 2>&1 || die 'Required tool is unavailable: bash.'

CHECK_DIRECTORY=$(mktemp -d "${TMPDIR:-/tmp}/cli-skills-pre-release.XXXXXX")
CHECK_DIRECTORY_OWNED=1
if [[ -d "$PROJECT_ROOT/dist" ]]; then
    DIST_PREEXISTED=1
fi

git -C "$PROJECT_ROOT" status --porcelain --untracked-files=all \
    > "$CHECK_DIRECTORY/status.before"
git -C "$PROJECT_ROOT" diff --binary > "$CHECK_DIRECTORY/unstaged.before"
git -C "$PROJECT_ROOT" diff --cached --binary > "$CHECK_DIRECTORY/staged.before"

CURRENT_PHASE='preflight safety checks'
[[ ! -L "$PROJECT_ROOT/dist" ]] || die 'dist/ is a symbolic link and cannot be cleaned safely.'
[[ ! -e "$PROJECT_ROOT/build" && ! -L "$PROJECT_ROOT/build" ]] ||
    die 'Pre-existing build/ output prevents safe cleanup.'
[[ ! -e "$PROJECT_ROOT/.cli-skills-build.lock" &&
    ! -L "$PROJECT_ROOT/.cli-skills-build.lock" ]] ||
    die 'A build lock exists; inspect it before running pre-release checks.'
[[ ! -e "$PROJECT_ROOT/dist/.cli-skills-build-manifest" &&
    ! -L "$PROJECT_ROOT/dist/.cli-skills-build-manifest" ]] ||
    die 'Pre-existing generated distributions must be safely cleared before this check.'
if [[ -d "$PROJECT_ROOT/dist" ]]; then
    shopt -s nullglob
    for artifact in "$PROJECT_ROOT/dist"/cli_skills-*.tar.gz \
        "$PROJECT_ROOT/dist"/cli_skills-*.whl \
        "$PROJECT_ROOT/dist"/.cli-skills-build.*; do
        [[ ! -e "$artifact" && ! -L "$artifact" ]] ||
            die "Pre-existing release output prevents safe cleanup: $artifact"
    done
fi
find "$PROJECT_ROOT/src" "$PROJECT_ROOT/tests" \
    \( -name '*.egg-info' -o -name '__pycache__' \) -print -quit \
    > "$CHECK_DIRECTORY/preexisting-python-artifacts"
[[ ! -s "$CHECK_DIRECTORY/preexisting-python-artifacts" ]] ||
    die 'Pre-existing egg-info or __pycache__ output prevents safe cleanup.'
CLEANUP_TARGETS_SAFE=1

CURRENT_PHASE='toolchain and dependency validation'
printf '==> [1/6] Validating toolchain, project structure, and lockfile\n'
uv --version
uv lock --check

CURRENT_PHASE='shell syntax validation'
printf '==> [2/6] Checking shell script syntax\n'
shopt -s nullglob
script_paths=("$PROJECT_ROOT/scripts"/*.sh)
(( ${#script_paths[@]} > 0 )) || die 'No release shell script found in scripts/.'
for script_path in "${script_paths[@]}"; do
    bash -n "$script_path"
done

CURRENT_PHASE='Python syntax and project configuration validation'
printf '==> [3/6] Parsing Python sources and project metadata\n'
UV_PROJECT_ENVIRONMENT="$CHECK_DIRECTORY/venv" \
    uv run --frozen python -c 'import ast, pathlib, tomllib; tomllib.load(open("pyproject.toml", "rb")); paths = list(pathlib.Path("src").rglob("*.py")) + list(pathlib.Path("tests").rglob("*.py")); [ast.parse(path.read_text(encoding="utf-8"), filename=str(path)) for path in paths]; print(f"Parsed {len(paths)} Python files and pyproject.toml")'

CURRENT_PHASE='complete unit test suite'
printf '==> [4/6] Running the project unittest suite\n'
UV_PROJECT_ENVIRONMENT="$CHECK_DIRECTORY/venv" \
    uv run --frozen python -m unittest discover -s tests
find "$PROJECT_ROOT/src" "$PROJECT_ROOT/tests" -type d \
    \( -name '*.egg-info' -o -name '__pycache__' \) -prune \
    -exec rm -rf -- {} +

CURRENT_PHASE='release build and artifact validation'
printf '==> [5/6] Building release distributions\n'
BUILD_ATTEMPTED=1
"$PROJECT_ROOT/scripts/build.sh"

CURRENT_PHASE='distribution metadata and ignore-rule validation'
printf '==> [6/6] Validating release metadata and generated artifacts\n'
shopt -s nullglob
sdists=("$PROJECT_ROOT/dist"/cli_skills-*.tar.gz)
wheels=("$PROJECT_ROOT/dist"/cli_skills-*.whl)
(( ${#sdists[@]} == 1 )) || die 'Expected exactly one source distribution in dist/.'
(( ${#wheels[@]} == 1 )) || die 'Expected exactly one wheel in dist/.'
[[ -s "${sdists[0]}" && -s "${wheels[0]}" ]] || die 'A release distribution is empty.'
for artifact in "${sdists[0]}" "${wheels[0]}" \
    "$PROJECT_ROOT/dist/.cli-skills-build-manifest"; do
    relative_artifact=${artifact#"$PROJECT_ROOT"/}
    git -C "$PROJECT_ROOT" check-ignore -q --no-index -- "$relative_artifact" ||
        die "Generated release output is not ignored by Git: $relative_artifact"
done
UV_PROJECT_ENVIRONMENT="$CHECK_DIRECTORY/venv" \
    uv run --frozen --with twine python -m twine check \
    "${sdists[0]}" "${wheels[0]}"
