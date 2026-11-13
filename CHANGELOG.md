# Changelog

## [0.10.8](https://github.com/Ogekuri/CLI-Skills/compare/v0.10.0..v0.10.8) - 2026-11-13
### ⛰️  Features
- Update gitalias config.
- add release artifact clean script [useReq] *(clean.sh)*
  Requirements: add PRJ-020 and DES-176..DES-185 for scripts/clean.sh.; clean.sh: remove generated sdist, wheel, SHA256SUMS, and staging directories from the release output directory (--output-dir, default dist/).; clean.sh: remove build/ and src *.egg-info directories; preserve foreign dist/ entries; refuse symlinked release output directory.; tests: add static Level 0 suite tests/test_clean_script.py (DES-185).

### 🐛  Bug Fixes
- request latest PyPI release on --upgrade [useReq] *(core)*
  Use the explicit cli-skills@latest specifier together with uv --upgrade so uv
  cannot report an older installed release as already installed and leave it
  unchanged.
  Add a reproducer unit test for the latest-release upgrade argv.
  Update WORKFLOW.md and REFERENCES.md.
- upgrade installed PyPI tool on --upgrade [useReq] *(core)*
  Run uv tool install cli-skills --upgrade so uv replaces the release already
  installed in the tool environment instead of auditing the stale version,
  restoring the documented --upgrade behavior.
  Add a reproducer unit test for the plain upgrade argv.
  Update WORKFLOW.md and REFERENCES.md.
- pin --dev upgrade to the latest GitHub release tag [useReq] *(core)*
  Resolve the latest GitHub release tag and pin the uv git source to it; Keep the unpinned source as a warned fallback when the release lookup fails; Add reproducer tests for pinned and fallback developer upgrades
- Remove files in dist/ dir.
- commit current dist artifacts [useReq] *(release)*
  run scripts/build.sh with the default dist/ output directory; add cli_skills-0.10.2 sdist and wheel to version control; add a reproducer test asserting the committed dist set matches project.version; keep packaging, workflow, and requirements unchanged
- clean nested egg-info and scope sdist to operational files [useReq] *(build.sh)*
  scripts/build.sh: egg-info cleanup now recurses under src/ (DES-147); removed -maxdepth 1.; scripts/build.sh: new sanitize_sdist phase drops setuptools-generated setup.cfg and src/*.egg-info sdist members.; MANIFEST.in: prune tests/, src/cli_skills.egg-info, and exclude MANIFEST.in from the sdist; .gitignore re-includes it.; tests/test_build_script.py: HDT Level 0 reproducer for recursive egg-info cleanup scope (DES-147).; Wheel content and entry points unchanged; sdist keeps DES-159 members; no src/ or REQUIREMENTS.md change.

### 🚜  Changes
- empty dist/ before building the new release [useReq] *(build)*
  Requirements: PRJ-021 and DES-143 updated; DES-148 retargeted; DES-199 added.
  Source code:
  scripts/build.sh: new purge_release_directory helper removes every
  remaining file, directory, and symbolic link inside the release output
  directory, including hidden entries, while preserving the directory.
  remove_generated_outputs now runs staging removal, archive removal, and
  the residual purge, so no artifact of an older version survives into the
  build phase; --clean shares the same emptying path.
  Removal stays confined to the release output directory; diagnostics and
  documentation updated accordingly.
- build release artifacts only in a temporary directory [useReq] *(pre-release-check)*
  Requirements: DES-084 and DES-173 updated; DES-198 added.
  Source code:
  scripts/pre-release-check.sh rejects a temporary release output directory
  located inside the repository tree, keeping the test build outside dist/.
  The embedded artifact validator no longer names a dist variable, so no
  executable code line references a dist/ entry.
  Tests: new Level 0 static suite tests/test_prerelease_check_script.py covering
  the temporary output directory, the containment guard, the single build
  invocation, and the absence of dist/ operations.
- remove pre-existing dist artifacts in pre-release-check [useReq] *(release-scripts)*
  Requirements: PRJ-014 and DES-143 updated; DES-173 removed; DES-194..DES-197 added.
  Source code:
  scripts/pre-release-check.sh now runs a dist-cleanup phase before the
  pre-run Git snapshot: validates the dist/ state, removes every
  *.tar.gz, *.whl, and .cli-skills-build.* entry, and verifies the
  removal, failing with status 1 on residual artifacts.
  Removal helpers are byte-identical to the scripts/build.sh bootstrap
  helpers (check_dist_state, remove_generated_outputs,
  remove_staging_leftovers, remove_generated_archives).
  scripts/build.sh documentation records the shared bootstrap helper set.
  Tests: new Level 0 static suite tests/test_prerelease_check_script.py.
- make dist artifacts optional in requirements [useReq] *(release)*
  run scripts/build.sh and commit cli_skills-0.10.2 sdist and wheel; remove PRJ-019 and drop repository-presence wording from PRJ-022, PRJ-023, DES-079, DES-192, DES-193; align release workflow and tests with workspace-provided dist artifacts; remove the test that required committed dist artifacts to exist
- consume committed dist artifacts without build [useReq] *(release)*
  release-pypi.yml reads pre-built dist/ artifacts from the tagged commit; remove build, toolchain setup, unit-test, and pre-release-check steps; verify committed sdist and wheel match project.version before publishing; publish committed packages to PyPI and GitHub release assets; update requirements PRJ-015/016 removal, PRJ-022/023, DES-078/079/088, DES-189..193; extend release workflow unit tests for the build-free automation
- integrate prior-build cleanup into build.sh [useReq] *(build)*
  remove scripts/clean.sh and tests/test_clean_script.py; run pre-build cleanup of dist archives of every name/version, staging dirs, build/, egg-info, and __pycache__; clean all intermediate artifacts through the EXIT trap after every build; update requirements PRJ-021, DES-142, DES-147, DES-186..188 and remove clean.sh requirements; extend build script unit tests for cleanup scope and ordering
- BREAKING CHANGE: Package bundled resources as cli_skills.resources [useReq] *(resources)*
  REQUIREMENTS.md: DES-020 and DES-157 redefine the wheel path of bundled resources as cli_skills/resources/.; pyproject.toml: map src/resources to package cli_skills.resources and exclude __pycache__ data.; catalog.py: RESOURCES_ROOT resolves cli_skills.resources instead of top-level resources.; pre-release-check.sh: wheel check expects cli_skills/resources/ and rejects a top-level resources/ member.; REFERENCES.md: regenerated for the updated catalog.py symbol lines.
  BREAKING: the wheel no longer installs a top-level resources package.
- BREAKING CHANGE: remove SHA256SUMS from release artifacts [useReq] *(build)*
  REQUIREMENTS: PRJ-019 drops dist/SHA256SUMS from versioned artifacts; DES-142 and DES-144 drop SHA256SUMS from generated-output removal and publication; DES-145 and DES-160 removed; DES-150 drops 'and verification'.; build.sh: stop writing SHA256SUMS, drop checksum verification phase; print sdist and wheel SHA-256 digests via sha256sum.; clean.sh: drop SHA256SUMS from release output removal patterns.; pre-release-check.sh: drop sha256sum -c checksum gate and sha256sum tool requirement.; tests: drop SHA256SUMS from test_clean_script removal-pattern assertion.
- track dist/ artifacts in Git and add --output-dir [useReq] *(build.sh)*
  Requirements: add PRJ-019 and DES-171..DES-175; modify DES-084, DES-087, DES-152, DES-160, DES-168, DES-170; remove DES-169.; build.sh: accept absolute --output-dir <path> selecting the release output directory (dist/ default).; pre-release-check.sh: build into a temporary release directory; never create, modify, or remove dist/ entries.; .gitignore: re-include dist/ and dist/**/*; remove dist/ exclusion rules.; tests: static Level 0 suites for --output-dir (DES-175) and .gitignore dist/ rules (DES-174).
- add dist build script and artifact-gated pre-release check [useReq] *(release-scripts)*
  Add scripts/build.sh: staged sdist/wheel build into dist/, archive integrity checks, SHA256SUMS publication with rollback, and --clean mode.; Rework scripts/pre-release-check.sh: toolchain and lockfile checks, syntax checks, unit tests, build.sh invocation, artifact content and twine validation, EXIT-trap cleanup with Git snapshot verification.; .gitignore: remove blanket dist/ exclusion; re-include dist/ and ignore generated release outputs through specific rules.; Requirements: revise PRJ-014, DES-084, DES-087; add PRJ-018 and DES-136 through DES-170.; Verification: ruff check clean on src and tests; 76/76 unit tests pass; failure-injection cases verified.
- add safe dist build pipeline and pre-release gate [useReq] *(release-scripts)*
  Add scripts/build.sh: staged sdist/wheel build, SHA-256 ownership manifest,
  atomic publication into dist/, digest-checked replacement and --clean-generated.
  Rework scripts/pre-release-check.sh: toolchain and lockfile validation, shell
  and Python syntax checks, full unittest suite, build.sh invocation, twine and
  artifact/ignore validation, snapshot-verified cleanup on success and failure.
  Update .gitignore inverse rules: keep dist/ traversable, ignore only generated
  archives, wheels, build manifest and staging directories.
  Requirements: revise PRJ-014, DES-084, DES-087; add DES-136 through DES-152.
- add safe dist build pipeline and pre-release gate [useReq] *(release-scripts)*
  Add scripts/build.sh: staged sdist/wheel build, SHA-256 ownership manifest,
  atomic publication into dist/, digest-checked replacement and --clean-generated.
  Rework scripts/pre-release-check.sh: toolchain and lockfile validation, shell
  and Python syntax checks, full unittest suite, build.sh invocation, twine and
  artifact/ignore validation, snapshot-verified cleanup on success and failure.
  Update .gitignore inverse rules: keep dist/ traversable, ignore only generated
  archives, wheels, build manifest and staging directories.
  Requirements: revise PRJ-014, DES-084, DES-087 and add DES-136 through DES-152.
- add safe artifact build and pre-release gate [useReq] *(release-scripts)*
- add schema-driven configuration CLI [useReq] *(config-cli)*
  Add canonical schema, atomic validated operations, and shared tree/table renderer.; Add --print/--info/--print-raw/--get/--set/--unset commands and help entries.; Update requirements, workflow call traces, and generated references.; Add golden, structural, table, and command-behavior tests.
- align --ver/--version output lines [useReq] *(version-report)*
  REQ-006/REQ-060/REQ-061: print Current Installed, Latest @ PyPI, and Latest @ GitHub lines with aligned values for --ver/--version.; REQ-070 (new): left-justify labels to common width via _REPORT_LABEL_WIDTH and the _report_line helper.; REQ-071 (new): Latest @ PyPI unavailable (<reason>) failure line.; REQ-066: GitHub failure value unknown (<reason>) under the Latest @ GitHub label.; DES-039: astra-uv-project skill spec now mandates the aligned report lines.; tests: exact-output assertion updated; full suite 29/29 green.
- add --force option to --upgrade commands [useReq] *(upgrade)*
  Accept the auxiliary --force option on --upgrade and --upgrade --dev/--develop.; Without --force, upgrades run the standard install/update process.; With --force, execute 'uv tool install cli-skills --force --reinstall --refresh'
  from PyPI, or the same options with --from git+... for the GitHub release.
  Requirements: update DES-038/DES-040/DES-081/REQ-010/REQ-063/REQ-064/REQ-065,
  add DES-103 and REQ-067..REQ-069, refresh the help template.
  Tests: cover forced PyPI/GitHub upgrades, forced manual command on non-Linux,
  and usage errors for invalid --force placements.
  Docs: update inline help template and README.md upgrade sections.

### ✨  Refactor
- Disable implicit data scan and drop sdist rewrite [useReq] *(packaging)*
  pyproject.toml: set include-package-data to false; package data is declared explicitly for cli_skills.resources, removing the setuptools warning for cli_skills.resources.skills.; scripts/build.sh: remove sanitize_sdist; the published sdist equals the python -m build output that the wheel was built from.; Wheel members unchanged (23); DES-020 and DES-157 wheel paths preserved; DES-159 sdist members preserved.; No requirement changes; no src/ changes; WORKFLOW.md and REFERENCES.md unchanged.

### ◀️  Revert
- Roll back branch to 063952e1 (063952e110a5f713779c51cf7a8f4dfcd3bd278c).
- Roll back branch to 2992ab6d (2992ab6db4bdc784c375b1c81268731ef9638a4c).
- Roll back branch to 2992ab6d (2992ab6db4bdc784c375b1c81268731ef9638a4c).
- Roll back branch to 2992ab6d (2992ab6db4bdc784c375b1c81268731ef9638a4c).

## [0.10.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.9.0..v0.10.0) - 2026-11-09
### ⛰️  Features
- add skills console-script entry point [useReq] *(packaging)*
  REQUIREMENTS.md: add PRJ-017, DES-101, DES-102 plus scope sentence
  for the additional skills executable
  pyproject.toml: declare skills in [project.scripts] bound to the
  same cli_skills.core:main entry point as cli-skills
  WORKFLOW.md: record both console-script launchers for PROC:main; Verification: static-check clean; 24/24 unit tests pass

### 🚜  Changes
- remove validate-supplied-guidance handling [useReq] *(prompt-skill-architect)*
  Remove the 'Validate supplied guidance' subsection from the
  prompt-skill-architect SKILL.md (guidance classification workflow).
  Remove requirement DES-093 from usereq/docs/REQUIREMENTS.md.; Regenerate usereq/docs/REFERENCES.md.; Verification: static-check clean; 24 unit tests passed.
- encode validated authoring guidance [useReq] *(prompt-skill-architect)*
  Change-ID: PI-useReq-20261109095120
  Add DES-093 through DES-100 and corresponding skill instructions.
  Preserve routing metadata, local packaging constraints, and external guidance.
  Validate metadata and catalog consistency; run 24 existing unit tests.
  Record baseline compliance gaps separately from the requested change.

## [0.9.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.8.0..v0.9.0) - 2026-11-08
### 🚜  Changes
- add opencode and copilot with alphabetical CLI listing [useReq] *(targets)*
  Extend supported CLIs from five to seven and order every CLI listing
  alphabetically.
  REQUIREMENTS.md: update PRJ-010 and scope list; add DES-090
  (opencode -> $HOME/.config/opencode/skills), DES-091 (copilot ->
  $HOME/.copilot/skills), DES-092 (alphabetical CLI listings).
  targets.py: add CopilotTarget and OpenCodeTarget adapters; build
  TARGETS registry in alphabetical key order.
  core.py/_unsupported and show.py/_cli_rows: document alphabetical
  listing (DES-092); README targets table updated and sorted.
- render tables with box-drawing borders [useReq] *(show)*
  Update DES-066: every show table must use box-drawing borders
  (┌─┬┐ top, ├─┼┤ header separator, │ verticals, └─┴┘ bottom)
  instead of +---+ ASCII borders.
  show.py render_table: three border builders over per-column ─ runs,
  single header separator, and one bottom border (no per-row rules).
  Update module and render_table Doxygen docs; WORKFLOW.md node text;
  regenerate REFERENCES.md.
- BREAKING CHANGE: remove prompt support keeping skills only [useReq] *(core)*
  Breaking change: complete removal of prompt installation, update,
  and maintenance; only skill management remains, with no backward
  compatibility or legacy logic.
  REQUIREMENTS.md: skills-only wording (PRJ/DES/REQ), remove DES-059,
  DES-060, DES-061, REQ-041, REQ-049, REQ-050; update help template.
  catalog/settings/targets/installer/show/core: drop prompts scanning,
  prompts config key, prompts_dir/install_prompts/remove_prompts,
  prompt summaries, records, tables, help lines, and prints.
  Delete src/resources/prompts and regenerate skills-only manifest.; Update README.md; update test_uninstall.py (RemovePromptTests
  removed), isolate config read in test_cli upgrade test.
- print GitHub latest failure reason on 404 rate limit [useReq] *(core)*
  Add REQ-066: --ver/--version must print 'GitHub latest: unknown
  (<reason>)' when the GitHub latest-release request fails, with the
  reason identifying the actual error.
  Add _failure_reason() to core.py: for HTTPError it decodes the JSON
  error body and surfaces the API message as 'HTTP <code>: <message>'
  (exposes 404 rate-limit causes); non-HTTP errors fall back to str(exc).
  Replace the GitHub 'unavailable' failure line with the required
  unknown(<reason>) syntax; PyPI line unchanged.
  Update WORKFLOW.md call trace and REFERENCES.md.

## [0.8.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.7.0..v0.8.0) - 2026-11-08
### 🐛  Bug Fixes
- replace invalid trove classifier blocking PyPI upload [useReq] *(metadata)*
  PyPI rejected the 0.7.0 upload with HTTP 400 because
  'Topic :: Software Development :: Configuration Management' is not an
  official trove classifier (0 occurrences in pypi.org/classifiers/).
  Replace it with its valid direct parent 'Topic :: Software Development'
  so project metadata satisfies DES-080 and unblocks PRJ-012/DES-079.
  Add HDT Level-0 reproducer suite tests/test_pyproject_classifiers.py
  validating every declared classifier against a verified official
  trove snapshot; suite runs offline and deterministically.

## [0.7.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.6.0..v0.7.0) - 2026-11-08
### 🐛  Bug Fixes
- pin astral-sh/setup-uv to published v9.0.0 [useReq] *(release)*
  The v10 major tag does not exist upstream, so the runner failed action
  resolution and blocked the unit-tests job and the whole release pipeline.
  Pin both setup-uv steps to v9.0.0 (newest published tag, node24 runtime;
  full semver because majors 8-9 have no floating major tag) satisfying CTN-010.
  Correct the DES-077 Node24 policy minimum for setup-uv to v7.0.0, the
  verified first node24 release (v6.8.0 is node20).
  Add reproducer test asserting every setup-uv pin and the policy minimum
  resolve against the verified upstream published tag set.

## [0.6.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.5.0..v0.6.0) - 2026-11-08
### 🚜  Changes
- BREAKING CHANGE: remove legacy argument orders and legacy program naming [useReq] *(cli)*
  Reject undocumented legacy argument orders: --help before a command
  name and --dev|--develop before --upgrade now exit 2; canonical
  <command> --help and --upgrade --dev|--develop forms are unchanged
  (REQ-033, DES-082, REQ-065).
  Remove legacy 'skills' program naming from PRJ-006 and the resources
  package docstring (PRJ-006).
  Add REQ-065 and DES-089; inline help verified user-facing only with
  live smoke checks; README verified free of legacy references; tests
  updated to canonical orders plus rejection coverage.
- gate release artifacts and publish on unit tests [useReq] *(release)*
  Add dedicated unit-tests job to release-pypi.yml running the
  project-defined unittest suite (PRJ-015).
  Make build-release depend on [check-branch, unit-tests] so failing
  tests skip dist build, attestation, GitHub release, and PyPI
  publish (PRJ-016).
  Add DES-088 conformance test asserting the test-job dependency and
  command in tests/test_release_workflow.py; verified by YAML graph
  check and full suite (24/24 OK).
- add pre-release-check.sh release gate [useReq] *(scripts)*
  Add scripts/pre-release-check.sh running the pre-release gate:
  build sdist+wheel with the release-workflow command into a temporary
  directory, twine check on the artifacts, and the project unittest
  suite (PRJ-014, DES-084..DES-086).
  EXIT trap removes the temporary build dir, build/, dist/, egg-info,
  and __pycache__ directories so the repository stays artifact-free on
  success and failure (DES-087).
  Verified with two full runs: exit 0, twine PASSED, 23/23 tests,
  repository left clean; stale dist/ and __pycache__ removed.
- publish to PyPI via trusted publishing and check PyPI releases [useReq] *(core)*
  Rename release-uvx.yml to release-pypi.yml; keep build, attestation,
  changelog, and GitHub release steps on every tagged branch and add
  OIDC Trusted Publishing to PyPI gated to master (PRJ-012, PRJ-013,
  DES-078, DES-079); pin setuptools>=77 for PEP 639 metadata (DES-080).
  Switch automatic release checks and --upgrade to PyPI; add
  --dev|--develop to upgrade from the latest tagged GitHub release;
  --ver/--version print installed plus PyPI and GitHub latest lines
  (REQ-002, REQ-010, REQ-043, REQ-059..REQ-064, DES-040, DES-042,
  DES-081..DES-083); README updated with PyPI install and a dedicated
  GitHub section.
- migrate release workflow actions to Node24 runtimes [useReq] *(release)*
  Bump actions to Node24-executing majors: checkout v4->v7,
  setup-python v5->v7, setup-uv v3->v10, attest-build-provenance
  v1->v4, action-gh-release v2->v3; changelog-builder v6 already
  runs node24. Runtimes verified from each action action.yml.
  Add CTN-010 (pin Node24-or-later action majors) and DES-077
  (conformance unit test) to REQUIREMENTS.md.
  Add tests/test_release_workflow.py verifying every referenced
  action major and the absence of Node20 fallback workaround envs.
- rename program to cli-skills and repository to CLI-Skills [useReq] *(core)*
  Rename package src/skills to src/cli_skills and launcher to
  scripts/cli-skills.sh; program name is now cli-skills (PRJ-001, CTN-003).
  Update repository references to https://github.com/Ogekuri/CLI-Skills
  in ENDPOINT, UPGRADE, pyproject URLs, README, and docs (CTN-005,
  REQ-002, REQ-010, REQ-013).
  Move user paths to ~/.cache/cli-skills and ~/.config/cli-skills
  (DES-009, DES-047); chain cli-skills install after --upgrade
  (REQ-043..REQ-046, REQ-058).
  Adapt test imports and assertions; regenerate REQUIREMENTS,
  WORKFLOW, and REFERENCES documentation.

### 📚  Documentation
- Update README.md file.

## [0.5.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.4.0..v0.5.0) - 2026-11-03
### 🐛  Bug Fixes
- harden bootstrap validation, cache semantics, verification bounds [useReq] *(astra-uv-project)*
  PHASE 0: validation gate for keyword values (name/path/URL safety); invalid input causes no writes; data-not-code substitution with TOML escaping (DES-015, DES-028-033); PHASE 1: gate precondition and project-root path confinement for all writes and renames; PHASE 4: explicit last-success/idle-time semantics; failure at t sets expiry t+86400 preserving prior successful timestamps or null (DES-043-046); Verification: separate build and execution checks with finite timeouts and PASS/FAIL/TIMEOUT/SKIPPED outcomes (DES-076)

### 🚜  Changes
- list installed skill and prompt names per CLI after upgrade [useReq] *(install)*
  Requirements: add REQ-057 (install lists installed skill names and prompt filenames per CLI) and REQ-058 (chained install report surfaces as --upgrade output); installer: InstallSummary carries sorted skill_names; install_target populates it; core: _install prints per-CLI installed names alongside counts; docstrings map REQ-057/REQ-058; WORKFLOW/REFERENCES updated for the new reporting surface

## [0.4.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.3.0..v0.4.0) - 2026-11-02
### ⛰️  Features
- add uninstall command removing installed skills and prompts [useReq] *(uninstall)*
  Add SRS requirements REQ-047..REQ-056 and PRJ-011 defining the reciprocal
  `uninstall` command of `install`, including help template coverage.
  Implement adapter removal primitives (CliTarget.remove_skills,
  remove_prompts), installer orchestration (uninstall_target,
  uninstall_enabled with prompt record clearing and per-CLI failure
  continuation), and core dispatch (_uninstall, help updates).
  Add HDT tests/test_uninstall.py suite; update WORKFLOW.md call traces
  and regenerate REFERENCES.md.

### 🚜  Changes
- fix skill rename and skeleton templating defects [useReq] *(astra-uv-project)*
  Align DES-001 archive path to assets/skell.tgz; Rename src/skell to src/%SRCDIR% in DES-033 and skill PHASE 1 (SHORTNAME/SRCDIR conflict); Declare core.py comment-only stub in DES-034 and skill PHASE 2; Delegate scripts/%SHORTNAME%.sh to python -m %SRCDIR% (DES-036, skeleton skell.sh); Template %AUTHOR% in skeleton pyproject authors (DES-074); Template %OWNER% in skeleton README URLs and skell.sh header (DES-075); Add bounded --help execution check (DES-076, skill verification step 5)

## [0.3.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.2.0..v0.3.0) - 2026-11-02
### 🐛  Bug Fixes
- Fix .gitignore file.

## [0.2.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.1.0..v0.2.0) - 2026-11-02
### 🚜  Changes
- chain skills install after successful --upgrade [useReq] *(core)*
  Requirements: add REQ-043..REQ-046 mandating post-upgrade execution of
  'skills install' when the enabled configuration is non-empty.
  Source: add SKILLS_INSTALL command constant and _post_upgrade_install();
  the --upgrade branch now chains the child 'skills install' after a
  successful Linux upgrade and returns its exit code.
  Docs: WORKFLOW.md adds PROC:skills-install unit and spawn edge;
  REFERENCES.md regenerated.

## [0.1.0](https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.1.0) - 2026-10-30
### ⛰️  Features
- add package inventory, CLI configuration, and install status report *(show)*
  Add skills show command with three aligned ASCII tables; Report manifest skills/prompts and per-CLI enabled state with install paths; Scan CLI destination directories to report OK, MISSING, STALE, UNSUPPORTED; Add show module, help text, requirements, workflow, and references; Preserve existing commands, configuration format, and installation behavior
- add common CLI skill and prompt installation [useReq] *(installer)*
  Add enable/disable/install commands backed by ~/.config/skills/config.json; Add modular adapters for pi, openclaw, codex, antigravity, and claude; Sync skill trees with overwrite and stale-file pruning; Track and prune installed prompt files per CLI; Extend requirements, workflow model, and references
- add skill scaffolding new Astral uv projects [useReq] *(astra-uv-project)*
  REQUIREMENTS.md: add PRJ-008, CTN-009, DES-025..DES-046 covering skill applicability, bundled assets/skell.tgz, PHASE 0-4 bootstrap keywords, extraction, substitution, renames, management commands, and online version check.; Add src/resources/skills/astra-uv-project/SKILL.md: English LLM-facing scaffold procedure with exact help template.; Bundle assets/skell.tgz as externally maintained skeleton input.; Regenerate src/resources/manifest.json catalog entry for the new skill.
- add skills and prompts JSON manifest [useReq] *(resources)*
  Add DES-021..DES-024 requirements for a src/resources manifest.
  Add src/skills/catalog.py generator (build_catalog/write_catalog).
  Add generated src/resources/manifest.json listing skills and prompts.
- distribute bundled LLM skills and prompts [useReq] *(resources)*
  Add PRJ-006/PRJ-007 and DES-014..DES-020 requirements for skills/prompts resources.
  Package src/resources (skills and prompts) into the distribution wheel.
  Add src/resources/__init__.py package marker and src/resources/prompts/README.md.
- Initial commit.

### 🐛  Bug Fixes
- Update gitignore file.

### 🚜  Changes
- filter install status and relativize skills paths [useReq] *(show)*
  Update REQ-038 and REQ-039 for home-relative skills paths and enabled-CLI status rows.; Render CLI skills paths relative to the user home directory.; Emit installation status rows only for enabled CLIs.; Refresh workflow traces and references.
- enforce canonical skill support layout [useReq] *(catalog)*
  Add DES-067..DES-073 defining canonical skill support subdirectories.; Validate skill roots and references/images layout during catalog generation.; Document the layout in prompt-skill-architect and README.; Surface layout rejections as installation errors and update runtime/workflow references.

### 📚  Documentation
- Update TODO.md.
- Update README.md.


# History

- \[0.1.0\]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.1.0
- \[0.2.0\]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.2.0
- \[0.3.0\]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.3.0
- \[0.4.0\]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.4.0
- \[0.5.0\]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.5.0
- \[0.6.0\]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.6.0
- \[0.7.0\]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.7.0
- \[0.8.0\]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.8.0
- \[0.9.0\]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.9.0
- \[0.10.0\]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.10.0
- \[0.10.8\]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.10.8

[0.1.0]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.1.0
[0.2.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.1.0..v0.2.0
[0.3.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.2.0..v0.3.0
[0.4.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.3.0..v0.4.0
[0.5.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.4.0..v0.5.0
[0.6.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.5.0..v0.6.0
[0.7.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.6.0..v0.7.0
[0.8.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.7.0..v0.8.0
[0.9.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.8.0..v0.9.0
[0.10.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.9.0..v0.10.0
[0.10.8]: https://github.com/Ogekuri/CLI-Skills/compare/v0.10.0..v0.10.8
