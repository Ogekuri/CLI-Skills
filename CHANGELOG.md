# Changelog

## [0.7.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.6.0..v0.7.0) - 2026-11-08
### 🐛  Bug Fixes
- pin astral-sh/setup-uv to published v9.0.0 [useReq] *(release)*
  - The v10 major tag does not exist upstream, so the runner failed action
  - resolution and blocked the unit-tests job and the whole release pipeline.
  - Pin both setup-uv steps to v9.0.0 (newest published tag, node24 runtime;
  - full semver because majors 8-9 have no floating major tag) satisfying CTN-010.
  - Correct the DES-077 Node24 policy minimum for setup-uv to v7.0.0, the
  - verified first node24 release (v6.8.0 is node20).
  - Add reproducer test asserting every setup-uv pin and the policy minimum
  - resolve against the verified upstream published tag set.

## [0.6.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.5.0..v0.6.0) - 2026-11-08
### 🚜  Changes
- BREAKING CHANGE: remove legacy argument orders and legacy program naming [useReq] *(cli)*
  - Reject undocumented legacy argument orders: --help before a command
  - name and --dev|--develop before --upgrade now exit 2; canonical
  - <command> --help and --upgrade --dev|--develop forms are unchanged
  - (REQ-033, DES-082, REQ-065).
  - Remove legacy 'skills' program naming from PRJ-006 and the resources
  - package docstring (PRJ-006).
  - Add REQ-065 and DES-089; inline help verified user-facing only with
  - live smoke checks; README verified free of legacy references; tests
  - updated to canonical orders plus rejection coverage.
- gate release artifacts and publish on unit tests [useReq] *(release)*
  - Add dedicated unit-tests job to release-pypi.yml running the
  - project-defined unittest suite (PRJ-015).
  - Make build-release depend on [check-branch, unit-tests] so failing
  - tests skip dist build, attestation, GitHub release, and PyPI
  - publish (PRJ-016).
  - Add DES-088 conformance test asserting the test-job dependency and
  - command in tests/test_release_workflow.py; verified by YAML graph
  - check and full suite (24/24 OK).
- add pre-release-check.sh release gate [useReq] *(scripts)*
  - Add scripts/pre-release-check.sh running the pre-release gate:
  - build sdist+wheel with the release-workflow command into a temporary
  - directory, twine check on the artifacts, and the project unittest
  - suite (PRJ-014, DES-084..DES-086).
  - EXIT trap removes the temporary build dir, build/, dist/, egg-info,
  - and __pycache__ directories so the repository stays artifact-free on
  - success and failure (DES-087).
  - Verified with two full runs: exit 0, twine PASSED, 23/23 tests,
  - repository left clean; stale dist/ and __pycache__ removed.
- publish to PyPI via trusted publishing and check PyPI releases [useReq] *(core)*
  - Rename release-uvx.yml to release-pypi.yml; keep build, attestation,
  - changelog, and GitHub release steps on every tagged branch and add
  - OIDC Trusted Publishing to PyPI gated to master (PRJ-012, PRJ-013,
  - DES-078, DES-079); pin setuptools>=77 for PEP 639 metadata (DES-080).
  - Switch automatic release checks and --upgrade to PyPI; add
  - --dev|--develop to upgrade from the latest tagged GitHub release;
  - --ver/--version print installed plus PyPI and GitHub latest lines
  - (REQ-002, REQ-010, REQ-043, REQ-059..REQ-064, DES-040, DES-042,
  - DES-081..DES-083); README updated with PyPI install and a dedicated
  - GitHub section.
- migrate release workflow actions to Node24 runtimes [useReq] *(release)*
  - Bump actions to Node24-executing majors: checkout v4->v7,
  - setup-python v5->v7, setup-uv v3->v10, attest-build-provenance
  - v1->v4, action-gh-release v2->v3; changelog-builder v6 already
  - runs node24. Runtimes verified from each action action.yml.
  - Add CTN-010 (pin Node24-or-later action majors) and DES-077
  - (conformance unit test) to REQUIREMENTS.md.
  - Add tests/test_release_workflow.py verifying every referenced
  - action major and the absence of Node20 fallback workaround envs.
- rename program to cli-skills and repository to CLI-Skills [useReq] *(core)*
  - Rename package src/skills to src/cli_skills and launcher to
  - scripts/cli-skills.sh; program name is now cli-skills (PRJ-001, CTN-003).
  - Update repository references to https://github.com/Ogekuri/CLI-Skills
  - in ENDPOINT, UPGRADE, pyproject URLs, README, and docs (CTN-005,
  - REQ-002, REQ-010, REQ-013).
  - Move user paths to ~/.cache/cli-skills and ~/.config/cli-skills
  - (DES-009, DES-047); chain cli-skills install after --upgrade
  - (REQ-043..REQ-046, REQ-058).
  - Adapt test imports and assertions; regenerate REQUIREMENTS,
  - WORKFLOW, and REFERENCES documentation.

### 📚  Documentation
- Update README.md file.

## [0.5.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.4.0..v0.5.0) - 2026-11-03
### 🐛  Bug Fixes
- harden bootstrap validation, cache semantics, verification bounds [useReq] *(astra-uv-project)*
  - PHASE 0: validation gate for keyword values (name/path/URL safety); invalid input causes no writes; data-not-code substitution with TOML escaping (DES-015, DES-028-033)
  - PHASE 1: gate precondition and project-root path confinement for all writes and renames
  - PHASE 4: explicit last-success/idle-time semantics; failure at t sets expiry t+86400 preserving prior successful timestamps or null (DES-043-046)
  - Verification: separate build and execution checks with finite timeouts and PASS/FAIL/TIMEOUT/SKIPPED outcomes (DES-076)

### 🚜  Changes
- list installed skill and prompt names per CLI after upgrade [useReq] *(install)*
  - Requirements: add REQ-057 (install lists installed skill names and prompt filenames per CLI) and REQ-058 (chained install report surfaces as --upgrade output)
  - installer: InstallSummary carries sorted skill_names; install_target populates it
  - core: _install prints per-CLI installed names alongside counts; docstrings map REQ-057/REQ-058
  - WORKFLOW/REFERENCES updated for the new reporting surface

## [0.4.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.3.0..v0.4.0) - 2026-11-02
### ⛰️  Features
- add uninstall command removing installed skills and prompts [useReq] *(uninstall)*
  - Add SRS requirements REQ-047..REQ-056 and PRJ-011 defining the reciprocal
  - `uninstall` command of `install`, including help template coverage.
  - Implement adapter removal primitives (CliTarget.remove_skills,
  - remove_prompts), installer orchestration (uninstall_target,
  - uninstall_enabled with prompt record clearing and per-CLI failure
  - continuation), and core dispatch (_uninstall, help updates).
  - Add HDT tests/test_uninstall.py suite; update WORKFLOW.md call traces
  - and regenerate REFERENCES.md.

### 🚜  Changes
- fix skill rename and skeleton templating defects [useReq] *(astra-uv-project)*
  - Align DES-001 archive path to assets/skell.tgz
  - Rename src/skell to src/%SRCDIR% in DES-033 and skill PHASE 1 (SHORTNAME/SRCDIR conflict)
  - Declare core.py comment-only stub in DES-034 and skill PHASE 2
  - Delegate scripts/%SHORTNAME%.sh to python -m %SRCDIR% (DES-036, skeleton skell.sh)
  - Template %AUTHOR% in skeleton pyproject authors (DES-074)
  - Template %OWNER% in skeleton README URLs and skell.sh header (DES-075)
  - Add bounded --help execution check (DES-076, skill verification step 5)

## [0.3.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.2.0..v0.3.0) - 2026-11-02
### 🐛  Bug Fixes
- Fix .gitignore file.

## [0.2.0](https://github.com/Ogekuri/CLI-Skills/compare/v0.1.0..v0.2.0) - 2026-11-02
### 🚜  Changes
- chain skills install after successful --upgrade [useReq] *(core)*
  - Requirements: add REQ-043..REQ-046 mandating post-upgrade execution of
  - 'skills install' when the enabled configuration is non-empty.
  - Source: add SKILLS_INSTALL command constant and _post_upgrade_install();
  - the --upgrade branch now chains the child 'skills install' after a
  - successful Linux upgrade and returns its exit code.
  - Docs: WORKFLOW.md adds PROC:skills-install unit and spawn edge;
  - REFERENCES.md regenerated.

## [0.1.0](https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.1.0) - 2026-10-30
### ⛰️  Features
- add package inventory, CLI configuration, and install status report *(show)*
  - Add skills show command with three aligned ASCII tables
  - Report manifest skills/prompts and per-CLI enabled state with install paths
  - Scan CLI destination directories to report OK, MISSING, STALE, UNSUPPORTED
  - Add show module, help text, requirements, workflow, and references
  - Preserve existing commands, configuration format, and installation behavior
- add common CLI skill and prompt installation [useReq] *(installer)*
  - Add enable/disable/install commands backed by ~/.config/skills/config.json
  - Add modular adapters for pi, openclaw, codex, antigravity, and claude
  - Sync skill trees with overwrite and stale-file pruning
  - Track and prune installed prompt files per CLI
  - Extend requirements, workflow model, and references
- add skill scaffolding new Astral uv projects [useReq] *(astra-uv-project)*
  - REQUIREMENTS.md: add PRJ-008, CTN-009, DES-025..DES-046 covering skill applicability, bundled assets/skell.tgz, PHASE 0-4 bootstrap keywords, extraction, substitution, renames, management commands, and online version check.
  - Add src/resources/skills/astra-uv-project/SKILL.md: English LLM-facing scaffold procedure with exact help template.
  - Bundle assets/skell.tgz as externally maintained skeleton input.
  - Regenerate src/resources/manifest.json catalog entry for the new skill.
- add skills and prompts JSON manifest [useReq] *(resources)*
  - Add DES-021..DES-024 requirements for a src/resources manifest.
  - Add src/skills/catalog.py generator (build_catalog/write_catalog).
  - Add generated src/resources/manifest.json listing skills and prompts.
- distribute bundled LLM skills and prompts [useReq] *(resources)*
  - Add PRJ-006/PRJ-007 and DES-014..DES-020 requirements for skills/prompts resources.
  - Package src/resources (skills and prompts) into the distribution wheel.
  - Add src/resources/__init__.py package marker and src/resources/prompts/README.md.
- Initial commit.

### 🐛  Bug Fixes
- Update gitignore file.

### 🚜  Changes
- filter install status and relativize skills paths [useReq] *(show)*
  - Update REQ-038 and REQ-039 for home-relative skills paths and enabled-CLI status rows.
  - Render CLI skills paths relative to the user home directory.
  - Emit installation status rows only for enabled CLIs.
  - Refresh workflow traces and references.
- enforce canonical skill support layout [useReq] *(catalog)*
  - Add DES-067..DES-073 defining canonical skill support subdirectories.
  - Validate skill roots and references/images layout during catalog generation.
  - Document the layout in prompt-skill-architect and README.
  - Surface layout rejections as installation errors and update runtime/workflow references.

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

[0.1.0]: https://github.com/Ogekuri/CLI-Skills/releases/tag/v0.1.0
[0.2.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.1.0..v0.2.0
[0.3.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.2.0..v0.3.0
[0.4.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.3.0..v0.4.0
[0.5.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.4.0..v0.5.0
[0.6.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.5.0..v0.6.0
[0.7.0]: https://github.com/Ogekuri/CLI-Skills/compare/v0.6.0..v0.7.0
