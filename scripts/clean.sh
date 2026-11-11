#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# VERSION: 0.10.2
# AUTHORS: Ogekuri

#/**
# * @file clean.sh
# * @brief Remove every artifact created by scripts/build.sh.
# * @details Removes the generated sdist, wheel, and staging
# *          directories from the release output directory (`dist/` by default or
# *          the absolute path given by --output-dir), removes the build/ entry of
# *          the repository root, and removes every *.egg-info directory under
# *          src/. Release output entries not matching the generated-output
# *          patterns are preserved, and the release output directory itself is
# *          never removed. A symbolic-link or non-directory release output
# *          directory aborts the run before any removal.
# * @satisfies PRJ-020 DES-176 DES-177 DES-178 DES-179 DES-180 DES-181 DES-182
# *            DES-183 DES-184
# */

set -Eeuo pipefail

#/**
# * @brief Original script location used to resolve the repository root.
# * @details BASH_SOURCE[0] preserves the invocation path, including spaces.
# * @satisfies DES-176
# */
SCRIPT_LOCATION=${BASH_SOURCE[0]}

#/**
# * @brief Canonical directory containing this script.
# * @satisfies DES-176
# */
SCRIPT_DIRECTORY=$(cd -- "$(dirname -- "$SCRIPT_LOCATION")" && pwd -P)

#/**
# * @brief Canonical repository root, parent of the scripts directory.
# * @satisfies DES-176
# */
PROJECT_ROOT=$(cd -- "$SCRIPT_DIRECTORY/.." && pwd -P)

#/**
# * @brief Release output directory; defaults to the canonical dist/ directory.
# * @details Replaced by the absolute path given to `--output-dir` during argument parsing.
# * @satisfies PRJ-020 DES-177
# */
DIST_DIRECTORY=$PROJECT_ROOT/dist

#/**
# * @brief Distribution file prefix derived from the pyproject project name.
# * @details Equals the project name with `-` replaced by `_`; validated against `^[A-Za-z0-9_]+$`.
# * @satisfies DES-178 DES-183
# */
DIST_PREFIX=

#/**
# * @brief Failure flag set to 1 when any matched entry could not be removed.
# * @details Removal continues for remaining entries; the final status is 1 when this flag is set.
# * @satisfies DES-184
# */
FAILED=0

#/**
# * @brief Print the usage diagnostic and terminate with status 2.
# * @details Accepts only the optional `--output-dir <absolute path>` argument.
# * @return {never} Exits with status 2.
# * @satisfies DES-177 DES-182
# */
usage() {
    printf 'Usage: scripts/clean.sh [--output-dir <absolute path>]\n' >&2
    exit 2
}

#/**
# * @brief Terminate with a diagnostic and status 1.
# * @param message {string} Failure description.
# * @return {never} Exits with status 1.
# * @satisfies DES-183
# */
fail() {
    printf 'ERROR: %s\n' "$1" >&2
    exit 1
}

#/**
# * @brief Report an unhandled failing command with its exit status.
# * @param status {int} Exit status of the failing command.
# * @param command {string} Text of the failing command from BASH_COMMAND.
# * @return {never} Exits with the failing status.
# */
on_error() {
    printf 'ERROR: command failed with status %s: %s\n' "$1" "$2" >&2
    exit "$1"
}

#/**
# * @brief Verify that every required executable is resolvable.
# * @details Collects every missing executable before failing so the diagnostic names all of them. Complexity O(R) for R required tools.
# * @return {None}
# * @throws {SystemExit} Via `fail` when any executable is missing.
# * @satisfies DES-183
# */
require_executables() {
    local tool
    local -a missing=()
    for tool in find rm sed dirname basename; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing+=("$tool")
        fi
    done
    if (( ${#missing[@]} > 0 )); then
        fail "missing required executables: ${missing[*]}"
    fi
}

#/**
# * @brief Derive the distribution file prefix from the pyproject project name.
# * @details Reads the single `name = "..."` line of pyproject.toml and sets DIST_PREFIX with `-` replaced by `_`.
# * @return {None}
# * @throws {SystemExit} Via `fail` when pyproject.toml is absent, the name is absent or ambiguous, or the name is unsupported.
# * @satisfies DES-178 DES-183
# */
resolve_project_prefix() {
    local names
    if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        fail "pyproject.toml is required to derive the distribution file prefix"
    fi
    names=$(sed -n 's/^name = "\([^"]*\)"$/\1/p' "$PROJECT_ROOT/pyproject.toml")
    if [[ -z $names || $names == *$'\n'* ]]; then
        fail "pyproject.toml must declare exactly one project name"
    fi
    DIST_PREFIX=${names//-/_}
    if [[ ! $DIST_PREFIX =~ ^[A-Za-z0-9_]+$ ]]; then
        fail "unsupported distribution name: $names"
    fi
}

#/**
# * @brief Parse the optional `--output-dir <absolute path>` argument.
# * @details Accepts zero arguments or one `--output-dir <path>` pair. Rejects a repeated option, a missing value, a relative path, and any other argument through `usage`. A valid path replaces DIST_DIRECTORY. Complexity O(A) for A arguments.
# * @param args {string...} Zero arguments, or `--output-dir <absolute path>`.
# * @return {None}
# * @throws {SystemExit} Via `usage` with status 2 for unsupported, repeated, or relative arguments.
# * @satisfies DES-177 DES-182
# */
parse_arguments() {
    local output_given=0
    local output=
    while (( $# > 0 )); do
        case $1 in
            --output-dir)
                if (( $# < 2 || output_given == 1 )); then
                    usage
                fi
                output_given=1
                output=$2
                shift 2
                ;;
            *)
                usage
                ;;
        esac
    done
    if (( output_given == 1 )); then
        if [[ $output != /* ]]; then
            usage
        fi
        DIST_DIRECTORY=$output
    fi
}

#/**
# * @brief Reject a symbolic-link or non-directory release output directory before any removal.
# * @details Aborts when DIST_DIRECTORY is a symbolic link or exists as a non-directory. A missing directory is accepted because it contains nothing to remove. Nothing is modified.
# * @return {None}
# * @throws {SystemExit} Via `fail` on an unsafe release output directory state.
# * @satisfies DES-181
# */
check_output_directory() {
    if [[ -L $DIST_DIRECTORY ]]; then
        fail "release output directory is a symbolic link; refusing to remove entries through it"
    fi
    if [[ -e $DIST_DIRECTORY && ! -d $DIST_DIRECTORY ]]; then
        fail "release output directory exists but is not a directory"
    fi
}

#/**
# * @brief Remove one filesystem entry recursively and record failures.
# * @details Skips the entry when it does not exist. Calls `rm -rf --` on the entry and sets FAILED to 1 on error; `rm` names the failing path on stderr. Complexity O(N) for N entries under the path.
# * @param path {string} Absolute path of the entry to remove.
# * @return {None}
# * @note Sets the global FAILED flag; never exits.
# * @satisfies DES-184
# */
remove_entry() {
    local path=$1
    if [[ -e $path || -L $path ]]; then
        if rm -rf -- "$path"; then
            printf 'Removed: %s\n' "$path"
        else
            printf 'ERROR: could not remove: %s\n' "$path" >&2
            FAILED=1
        fi
    fi
}

#/**
# * @brief Remove generated release outputs from the release output directory.
# * @details Removes `<DIST_PREFIX>-*.tar.gz`, `<DIST_PREFIX>-*.whl`, and `.cli-skills-build.*` staging directories from DIST_DIRECTORY. Glob expansion uses nullglob so absent patterns vanish. Every other entry is preserved. Complexity O(M) for M matched entries.
# * @return {None}
# * @satisfies DES-178 DES-180 DES-184
# */
remove_release_outputs() {
    local entry
    local -a matches=()
    shopt -s nullglob
    matches=("$DIST_DIRECTORY/$DIST_PREFIX"-*.tar.gz "$DIST_DIRECTORY/$DIST_PREFIX"-*.whl "$DIST_DIRECTORY"/.cli-skills-build.*)
    shopt -u nullglob
    for entry in "${matches[@]}"; do
        remove_entry "$entry"
    done
}

#/**
# * @brief Remove the repository build/ entry and every src egg-info directory.
# * @details Removes `$PROJECT_ROOT/build` and runs `find` over `$PROJECT_ROOT/src` with `-prune` to remove every `*.egg-info` directory without a depth limit. A find or rm failure sets FAILED to 1. Complexity O(D) for D matched directories.
# * @return {None}
# * @satisfies DES-179 DES-184
# */
remove_build_outputs() {
    remove_entry "$PROJECT_ROOT/build"
    if [[ -d $PROJECT_ROOT/src ]]; then
        if ! find "$PROJECT_ROOT/src" -type d -name '*.egg-info' -prune -exec rm -rf -- {} +; then
            printf 'ERROR: could not remove src egg-info directories.\n' >&2
            FAILED=1
        fi
    fi
}

#/**
# * @brief Execute the clean sequence end to end.
# * @details Parses arguments, changes to the repository root, validates executables and the project name, refuses an unsafe release output directory, removes release outputs, then removes build outputs. Every removal precedes the final status decision.
# * @param args {string...} Zero arguments, or `--output-dir <absolute path>`.
# * @return {None}
# * @throws {SystemExit} Via `usage`, `fail`, or the final status 1 when any removal failed.
# * @satisfies PRJ-020 DES-176 DES-177 DES-181 DES-183 DES-184
# */
main() {
    parse_arguments "$@"
    cd -- "$PROJECT_ROOT"
    require_executables
    resolve_project_prefix
    check_output_directory
    remove_release_outputs
    remove_build_outputs
    if (( FAILED == 1 )); then
        printf 'scripts/clean.sh: FAIL (one or more artifacts could not be removed).\n' >&2
        exit 1
    fi
    printf 'scripts/clean.sh: PASS.\n'
}

trap 'on_error "$?" "$BASH_COMMAND"' ERR

main "$@"
