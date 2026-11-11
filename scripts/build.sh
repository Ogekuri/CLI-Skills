#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# VERSION: 0.10.2
# AUTHORS: Ogekuri

#/**
# * @file build.sh
# * @brief Generate the cli-skills release distribution set in dist/.
# * @details Builds the sdist and wheel with the release build command into a
# *          staging directory inside dist/, validates the staged archives,
# *          replaces previously generated outputs of this project, publishes the
# *          sdist and wheel, and prints their SHA-256 digests. Intermediate build/ and src egg-info outputs are removed
# *          on every exit path. The --clean option removes only generated dist/
# *          outputs and leaves every other dist/ entry untouched. The
# *          --output-dir option replaces dist/ with an absolute release output
# *          directory for every phase.
# * @satisfies PRJ-018 DES-136 DES-137 DES-138 DES-139 DES-140 DES-141 DES-142
# *            DES-143 DES-144 DES-146 DES-147 DES-148 DES-149 DES-150
# *            DES-151 DES-171 DES-172
# */

set -Eeuo pipefail

#/**
# * @brief Original script location used to resolve the repository root.
# * @details BASH_SOURCE[0] preserves the invocation path, including spaces.
# * @satisfies DES-136
# */
SCRIPT_LOCATION=${BASH_SOURCE[0]}

#/**
# * @brief Canonical directory containing this script.
# * @satisfies DES-136
# */
SCRIPT_DIRECTORY=$(cd -- "$(dirname -- "$SCRIPT_LOCATION")" && pwd -P)

#/**
# * @brief Canonical repository root, parent of the scripts directory.
# * @satisfies DES-136
# */
PROJECT_ROOT=$(cd -- "$SCRIPT_DIRECTORY/.." && pwd -P)

#/**
# * @brief Release output directory; defaults to the canonical dist/ directory.
# * @details Replaced by the absolute path given to `--output-dir` during argument parsing. Every `dist/` reference in DES-139 through DES-150 denotes this directory.
# * @satisfies PRJ-018 DES-171
# */
DIST_DIRECTORY=$PROJECT_ROOT/dist

#/**
# * @brief Requested mode: `build` by default or `clean` for `--clean`.
# */
MODE=build

#/**
# * @brief Active phase identifier reported by diagnostics and the final summary.
# */
CURRENT_PHASE=arguments

#/**
# * @brief Distribution file prefix derived from the pyproject project name.
# * @details Equals the project name with `-` replaced by `_`; validated against `^[A-Za-z0-9_]+$`.
# * @satisfies DES-142
# */
DIST_PREFIX=

#/**
# * @brief Flag set to 1 when this invocation created dist/.
# * @satisfies PRJ-018
# */
DIST_CREATED=0

#/**
# * @brief Flag set to 1 after preflight accepts the build/ state, enabling intermediate cleanup.
# * @satisfies DES-147
# */
CLEANUP_ENABLED=0

#/**
# * @brief Temporary directory owning the isolated uv project environment.
# * @satisfies DES-138
# */
ENVIRONMENT_DIRECTORY=

#/**
# * @brief Staging directory inside dist/ receiving the build output.
# * @satisfies DES-139
# */
STAGING_DIRECTORY=

#/**
# * @brief File name of the staged sdist validated before publication.
# */
STAGED_SDIST_NAME=

#/**
# * @brief File name of the staged wheel validated before publication.
# */
STAGED_WHEEL_NAME=

#/**
# * @brief Absolute paths of the artifacts moved into dist/ by this invocation.
# * @satisfies DES-144
# */
PUBLISHED_FILES=()

#/**
# * @brief Print the usage diagnostic and terminate with status 2.
# * @details Accepts `--clean` and `--output-dir <absolute path>` in any order; nothing else is accepted.
# * @return {never} Exits with status 2.
# * @satisfies DES-149 DES-171 DES-172
# */
usage() {
    printf 'Usage: scripts/build.sh [--clean] [--output-dir <absolute path>]\n' >&2
    exit 2
}

#/**
# * @brief Start a named phase and report it on stdout.
# * @param phase_id {string} Stable phase identifier stored in CURRENT_PHASE.
# * @param label {string} Human-readable phase description.
# * @return {None}
# */
begin_phase() {
    CURRENT_PHASE=$1
    printf '==> [%s] %s\n' "$1" "$2"
}

#/**
# * @brief Terminate with a phase-identified diagnostic.
# * @param message {string} Failure description.
# * @return {never} Exits with status 1; the EXIT trap performs cleanup.
# * @satisfies DES-151
# */
fail() {
    printf 'ERROR: [%s] %s\n' "$CURRENT_PHASE" "$1" >&2
    exit 1
}

#/**
# * @brief Report an unhandled failing command with its phase and exit status.
# * @param status {int} Exit status of the failing command.
# * @param command {string} Text of the failing command from BASH_COMMAND.
# * @return {never} Exits with the failing status.
# * @satisfies DES-151
# */
on_error() {
    printf 'ERROR: [%s] command failed with status %s: %s\n' "$CURRENT_PHASE" "$1" "$2" >&2
    exit "$1"
}

#/**
# * @brief Verify that every required executable is resolvable.
# * @details Collects every missing executable before failing so the diagnostic names all of them. Complexity O(R) for R required tools.
# * @return {None}
# * @throws {SystemExit} Via `fail` when any executable is missing.
# * @satisfies DES-137
# */
require_executables() {
    local tool
    local -a missing=()
    for tool in uv sha256sum mktemp mv rm rmdir sed find dirname basename cat; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing+=("$tool")
        fi
    done
    if (( ${#missing[@]} > 0 )); then
        fail "missing required executables: ${missing[*]}"
    fi
}

#/**
# * @brief Validate the project layout and derive the distribution file prefix.
# * @details Requires pyproject.toml, uv.lock, and src/cli_skills. Reads the single `name = "..."` line of pyproject.toml and derives DIST_PREFIX by replacing `-` with `_`.
# * @return {None}
# * @throws {SystemExit} Via `fail` when the layout is incomplete or the name is unsupported.
# * @satisfies DES-136 DES-142
# */
resolve_project() {
    local names
    if [[ ! -f "$PROJECT_ROOT/pyproject.toml" || ! -f "$PROJECT_ROOT/uv.lock" || ! -d "$PROJECT_ROOT/src/cli_skills" ]]; then
        fail "project layout incomplete: pyproject.toml, uv.lock, and src/cli_skills are required"
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
# * @brief Reject unsafe release output directory states before any removal or write.
# * @details Aborts when the release output directory (DIST_DIRECTORY) is a symbolic link or exists as a non-directory.
# * @return {None}
# * @throws {SystemExit} Via `fail` on an unsafe dist/ state.
# * @satisfies DES-143
# */
check_dist_state() {
    if [[ -L $DIST_DIRECTORY ]]; then
        fail "release output directory is a symbolic link; refusing to remove or write through it"
    fi
    if [[ -e $DIST_DIRECTORY && ! -d $DIST_DIRECTORY ]]; then
        fail "release output directory exists but is not a directory"
    fi
}

#/**
# * @brief Remove stale staging directories left by interrupted earlier builds.
# * @details Matches `dist/.cli-skills-build.*` only. Complexity O(M) for M matches.
# * @return {None}
# * @throws {SystemExit} Via `fail` when a match cannot be removed.
# * @satisfies DES-139 DES-143
# */
remove_staging_leftovers() {
    local entry
    local -a matches=()
    shopt -s nullglob
    matches=("$DIST_DIRECTORY"/.cli-skills-build.*)
    shopt -u nullglob
    for entry in "${matches[@]}"; do
        if ! rm -rf -- "$entry"; then
            fail "could not remove stale staging directory: $entry"
        fi
    done
}

#/**
# * @brief Remove previously generated distribution archives.
# * @details Removes `dist/<DIST_PREFIX>-*.tar.gz` and `dist/<DIST_PREFIX>-*.whl` when present. Every other dist/ entry is preserved.
# * @return {None}
# * @throws {SystemExit} Via `fail` when a generated file cannot be removed.
# * @satisfies DES-142 DES-143
# */
remove_generated_archives() {
    local entry
    local -a matches=()
    shopt -s nullglob
    matches=("$DIST_DIRECTORY/$DIST_PREFIX"-*.tar.gz "$DIST_DIRECTORY/$DIST_PREFIX"-*.whl)
    shopt -u nullglob
    for entry in "${matches[@]}"; do
        if [[ -e $entry || -L $entry ]]; then
            if ! rm -f -- "$entry"; then
                fail "could not remove generated output: $entry"
            fi
        fi
    done
}

#/**
# * @brief Execute the `--clean` mode.
# * @details Removes staging leftovers and generated archives from dist/ only. Exits through the EXIT trap with status 0 on success.
# * @return {None}
# * @satisfies DES-148 DES-143
# */
run_clean() {
    begin_phase clean "Removing generated release outputs from dist/"
    remove_staging_leftovers
    remove_generated_archives
    printf 'Generated release outputs removed; other dist/ entries were preserved.\n'
}

#/**
# * @brief Validate the staged archive set before publication.
# * @details Requires exactly one sdist and one wheel whose names start with DIST_PREFIX-. Checks sdist gzip/tar readability and wheel CRC integrity through an isolated uv Python. Sets STAGED_SDIST_NAME and STAGED_WHEEL_NAME. Complexity O(A) where A is the archive member count.
# * @return {None}
# * @throws {SystemExit} Via `fail` on count, name, or integrity violations.
# * @satisfies DES-140 DES-141
# */
validate_staged_archives() {
    local -a sdists=()
    local -a wheels=()
    begin_phase validation "Validating staged archive count, names, and integrity"
    shopt -s nullglob
    sdists=("$STAGING_DIRECTORY"/*.tar.gz)
    wheels=("$STAGING_DIRECTORY"/*.whl)
    shopt -u nullglob
    if (( ${#sdists[@]} != 1 || ${#wheels[@]} != 1 )); then
        fail "expected exactly one sdist and one wheel, found ${#sdists[@]} sdist(s) and ${#wheels[@]} wheel(s)"
    fi
    STAGED_SDIST_NAME=$(basename -- "${sdists[0]}")
    STAGED_WHEEL_NAME=$(basename -- "${wheels[0]}")
    if [[ $STAGED_SDIST_NAME != "$DIST_PREFIX"-* || $STAGED_WHEEL_NAME != "$DIST_PREFIX"-* ]]; then
        fail "staged artifact names do not start with $DIST_PREFIX-"
    fi
    uv run --no-project python - "${sdists[0]}" "${wheels[0]}" <<'PY'
import sys
import tarfile
import zipfile

sdist_path, wheel_path = sys.argv[1], sys.argv[2]
with tarfile.open(sdist_path, "r:gz") as sdist:
    if not sdist.getmembers():
        raise SystemExit("sdist archive has no members")
with zipfile.ZipFile(wheel_path) as wheel:
    corrupt_member = wheel.testzip()
    if corrupt_member is not None:
        raise SystemExit(f"wheel member failed CRC check: {corrupt_member}")
    if not wheel.namelist():
        raise SystemExit("wheel archive has no members")
print("archive integrity: PASS")
PY
}

#/**
# * @brief Run the isolated build and stage the sdist and wheel.
# * @details Creates the temporary uv environment outside the repository tree and the staging directory inside dist/, then runs the release build command with `--outdir` pointing at the staging directory. Failure exits through `on_error`.
# * @return {None}
# * @satisfies DES-138 DES-139
# */
build_into_staging() {
    begin_phase build "Building sdist and wheel into the staging directory"
    ENVIRONMENT_DIRECTORY=$(mktemp -d "${TMPDIR:-/tmp}/cli-skills-build.XXXXXX")
    STAGING_DIRECTORY=$(mktemp -d "$DIST_DIRECTORY/.cli-skills-build.XXXXXX")
    UV_PROJECT_ENVIRONMENT="$ENVIRONMENT_DIRECTORY/venv" \
        uv run --frozen --with build python -m build --outdir "$STAGING_DIRECTORY"
}

#/**
# * @brief Remove setuptools-generated non-operational members from the staged sdist.
# * @details Requires exactly one staged sdist. Rewrites the archive without the root `setup.cfg` member and every member under `src/*.egg-info/`, which setuptools emits during the sdist step after manifest pruning is applied. The rewrite runs in an isolated uv Python with `tarfile`, targets a sibling temporary archive inside the staging directory, and replaces the original with `os.replace`. Member metadata and payloads of retained entries are copied unchanged. Complexity O(M) where M is the archive member count.
# * @return {None}
# * @throws {SystemExit} Via `fail` when the staged sdist count differs from one; the Python rewrite exits with status 1 on an empty or unreadable archive.
# * @satisfies PRJ-018 DES-008 DES-037 DES-141 DES-159
# */
sanitize_sdist() {
    local -a sdists=()
    begin_phase sanitization "Removing setuptools-generated setup.cfg and egg-info members from the staged sdist"
    shopt -s nullglob
    sdists=("$STAGING_DIRECTORY"/*.tar.gz)
    shopt -u nullglob
    if (( ${#sdists[@]} != 1 )); then
        fail "expected exactly one staged sdist before sanitization, found ${#sdists[@]} sdist(s)"
    fi
    uv run --no-project python - "${sdists[0]}" <<'PY'
import os
import sys
import tarfile

source_path = sys.argv[1]
temporary_path = source_path + ".sanitized"
with tarfile.open(source_path, "r:gz") as source:
    members = source.getmembers()
    if not members:
        raise SystemExit("sdist archive has no members")
    root = members[0].name.split("/", 1)[0]
    with tarfile.open(temporary_path, "w:gz", format=tarfile.PAX_FORMAT) as target:
        for member in members:
            parts = member.name.split("/")
            if member.name == f"{root}/setup.cfg":
                continue
            if len(parts) >= 3 and parts[0] == root and parts[1] == "src" and parts[2].endswith(".egg-info"):
                continue
            payload = source.extractfile(member) if member.isfile() else None
            target.addfile(member, payload)
os.replace(temporary_path, source_path)
print("sdist sanitization: PASS")
PY
}

#/**
# * @brief Remove previous generated archives and publish the new artifacts.
# * @details Removes previous generated outputs and moves the staged sdist and wheel into dist/ with same-filesystem renames. Each published path is recorded for rollback.
# * @return {None}
# * @satisfies DES-142 DES-144
# */
publish_distributions() {
    local name
    begin_phase publication "Publishing artifacts into dist/"
    remove_generated_archives
    for name in "$STAGED_SDIST_NAME" "$STAGED_WHEEL_NAME"; do
        mv -- "$STAGING_DIRECTORY/$name" "$DIST_DIRECTORY/$name"
        PUBLISHED_FILES+=("$DIST_DIRECTORY/$name")
    done
}

#/**
# * @brief Print the published artifact names and SHA-256 digests.
# * @details Computes SHA-256 digests of the published sdist and wheel inside dist/ and emits one `<digest>  <name>` line per artifact.
# * @return {None}
# * @satisfies DES-150
# */
print_summary() {
    begin_phase summary "Published release artifacts (SHA-256 digests and names)"
    (cd -- "$DIST_DIRECTORY" && sha256sum -- "$STAGED_SDIST_NAME" "$STAGED_WHEEL_NAME")
}

#/**
# * @brief Execute the default build mode end to end.
# * @details Refuses a pre-existing build/ entry, enables intermediate cleanup, prepares dist/, builds into staging, validates, publishes, and prints the summary.
# * @return {None}
# * @throws {SystemExit} Via `fail` or `on_error` on any mandatory phase failure.
# * @satisfies DES-146 DES-147 DES-151
# */
run_build() {
    if [[ -e $PROJECT_ROOT/build || -L $PROJECT_ROOT/build ]]; then
        fail "build/ exists in the repository root; refusing to modify it"
    fi
    CLEANUP_ENABLED=1
    if [[ ! -e $DIST_DIRECTORY ]]; then
        mkdir -- "$DIST_DIRECTORY"
        DIST_CREATED=1
    fi
    remove_staging_leftovers
    build_into_staging
    sanitize_sdist
    validate_staged_archives
    publish_distributions
    print_summary
}

#/**
# * @brief Remove intermediate and staging outputs owned by this invocation.
# * @details Rolls back published files when the run failed; removes the staging directory, the temporary uv environment, and, when CLEANUP_ENABLED is 1, the repository build/ directory and every *.egg-info directory under src/; removes dist/ only when this run created it, the run failed, and it is empty. Complexity O(P) where P is the published file count.
# * @param failed {int} 1 when the run failed; otherwise 0.
# * @return {int} 0 when every owned output is removed; 1 otherwise.
# * @satisfies DES-144 DES-147 DES-151
# */
cleanup_owned_outputs() {
    local failed=$1
    local status=0
    local path
    if [[ -n $STAGING_DIRECTORY && -e $STAGING_DIRECTORY ]]; then
        if ! rm -rf -- "$STAGING_DIRECTORY"; then
            printf 'ERROR: [cleanup] could not remove staging directory: %s\n' "$STAGING_DIRECTORY" >&2
            status=1
        fi
    fi
    if [[ -n $ENVIRONMENT_DIRECTORY && -e $ENVIRONMENT_DIRECTORY ]]; then
        if ! rm -rf -- "$ENVIRONMENT_DIRECTORY"; then
            printf 'ERROR: [cleanup] could not remove temporary uv environment: %s\n' "$ENVIRONMENT_DIRECTORY" >&2
            status=1
        fi
    fi
    if (( failed == 1 )); then
        for path in "${PUBLISHED_FILES[@]}"; do
            if [[ -e $path ]]; then
                if ! rm -f -- "$path"; then
                    printf 'ERROR: [cleanup] could not roll back published file: %s\n' "$path" >&2
                    status=1
                fi
            fi
        done
    fi
    if (( CLEANUP_ENABLED == 1 )); then
        if [[ -e $PROJECT_ROOT/build || -L $PROJECT_ROOT/build ]]; then
            if ! rm -rf -- "$PROJECT_ROOT/build"; then
                printf 'ERROR: [cleanup] could not remove build/ intermediate directory.\n' >&2
                status=1
            fi
        fi
        if ! find "$PROJECT_ROOT/src" -type d -name '*.egg-info' -prune -exec rm -rf -- {} +; then
            printf 'ERROR: [cleanup] could not remove src egg-info directories.\n' >&2
            status=1
        fi
    fi
    if (( failed == 1 && DIST_CREATED == 1 )); then
        if [[ -d $DIST_DIRECTORY ]]; then
            if [[ -z $(find "$DIST_DIRECTORY" -mindepth 1 -print -quit) ]]; then
                if ! rmdir -- "$DIST_DIRECTORY"; then
                    printf 'ERROR: [cleanup] could not remove empty dist/ created by this run.\n' >&2
                    status=1
                fi
            else
                printf 'WARNING: [cleanup] dist/ created by this run contains foreign entries; kept.\n' >&2
            fi
        fi
    fi
    return "$status"
}

#/**
# * @brief Terminate the script while preserving the original status and enforcing cleanup.
# * @details Runs as the EXIT trap. Captures the status first, clears all traps, runs cleanup, reports cleanup failure as status 1 only when the run otherwise succeeded, and prints a PASS or phase-identified FAIL summary.
# * @return {never} Exits with the final status.
# * @satisfies DES-151 DES-147
# */
finish() {
    local status=$?
    local failed_phase=$CURRENT_PHASE
    local failed=0
    trap - EXIT ERR INT TERM HUP
    if (( status != 0 )); then
        failed=1
    fi
    if ! cleanup_owned_outputs "$failed"; then
        if (( status == 0 )); then
            status=1
            failed_phase=cleanup
        fi
    fi
    if (( status == 0 )); then
        printf 'scripts/build.sh (%s): PASS.\n' "$MODE"
    else
        printf 'scripts/build.sh (%s): FAIL at phase %s (status %d).\n' "$MODE" "$failed_phase" "$status" >&2
    fi
    exit "$status"
}

#/**
# * @brief Parse the optional `--clean` and `--output-dir <path>` arguments.
# * @details Accepts `--clean` and one `--output-dir <path>` pair in any order. Rejects repeated `--output-dir`, a missing value, a relative path, and unknown arguments through `usage`. Sets MODE to `clean` or `build`; a valid `--output-dir` path replaces DIST_DIRECTORY. Complexity O(A) for A arguments.
# * @param args {string...} Zero or more of `--clean` and `--output-dir <absolute path>`.
# * @return {None}
# * @throws {SystemExit} Via `usage` with status 2 for unsupported, repeated, or relative arguments.
# * @satisfies DES-148 DES-149 DES-171 DES-172
# */
parse_arguments() {
    local clean=0
    local output_given=0
    local output=
    while (( $# > 0 )); do
        case $1 in
            --clean)
                clean=1
                shift
                ;;
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
    if (( clean == 1 )); then
        MODE=clean
    else
        MODE=build
    fi
}

#/**
# * @brief Validate the environment and dispatch the requested mode.
# * @details Parses arguments, changes to the repository root, validates executables, project layout, and the release output directory state, then dispatches clean or build mode.
# * @return {None}
# * @throws {SystemExit} Via `usage` for unsupported arguments and via `fail` for preflight failures.
# * @satisfies DES-148 DES-149 DES-171
# */
main() {
    parse_arguments "$@"
    cd -- "$PROJECT_ROOT"
    begin_phase preflight "Validating executables, project layout, and dist/ state"
    require_executables
    resolve_project
    check_dist_state
    if [[ $MODE == clean ]]; then
        run_clean
    else
        run_build
    fi
}

trap finish EXIT
trap 'on_error "$?" "$BASH_COMMAND"' ERR
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

main "$@"
