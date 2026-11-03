# Changelog

## [0.5.0](https://github.com/Ogekuri/SKILLs/compare/v0.4.0..v0.5.0) - 2026-11-03
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

## [0.4.0](https://github.com/Ogekuri/SKILLs/compare/v0.3.0..v0.4.0) - 2026-11-02
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

## [0.3.0](https://github.com/Ogekuri/SKILLs/compare/v0.2.0..v0.3.0) - 2026-11-02
### 🐛  Bug Fixes
- Fix .gitignore file.

## [0.2.0](https://github.com/Ogekuri/SKILLs/compare/v0.1.0..v0.2.0) - 2026-11-02
### 🚜  Changes
- chain skills install after successful --upgrade [useReq] *(core)*
  - Requirements: add REQ-043..REQ-046 mandating post-upgrade execution of
  - 'skills install' when the enabled configuration is non-empty.
  - Source: add SKILLS_INSTALL command constant and _post_upgrade_install();
  - the --upgrade branch now chains the child 'skills install' after a
  - successful Linux upgrade and returns its exit code.
  - Docs: WORKFLOW.md adds PROC:skills-install unit and spawn edge;
  - REFERENCES.md regenerated.

## [0.1.0](https://github.com/Ogekuri/SKILLs/releases/tag/v0.1.0) - 2026-10-30
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

- \[0.1.0\]: https://github.com/Ogekuri/SKILLs/releases/tag/v0.1.0
- \[0.2.0\]: https://github.com/Ogekuri/SKILLs/releases/tag/v0.2.0
- \[0.3.0\]: https://github.com/Ogekuri/SKILLs/releases/tag/v0.3.0
- \[0.4.0\]: https://github.com/Ogekuri/SKILLs/releases/tag/v0.4.0
- \[0.5.0\]: https://github.com/Ogekuri/SKILLs/releases/tag/v0.5.0

[0.1.0]: https://github.com/Ogekuri/SKILLs/releases/tag/v0.1.0
[0.2.0]: https://github.com/Ogekuri/SKILLs/compare/v0.1.0..v0.2.0
[0.3.0]: https://github.com/Ogekuri/SKILLs/compare/v0.2.0..v0.3.0
[0.4.0]: https://github.com/Ogekuri/SKILLs/compare/v0.3.0..v0.4.0
[0.5.0]: https://github.com/Ogekuri/SKILLs/compare/v0.4.0..v0.5.0
