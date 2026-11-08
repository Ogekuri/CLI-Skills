"""Uninstall command unit tests: adapter removal, target uninstallation, enabled orchestration, and CLI dispatch."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cli_skills import core, installer
from cli_skills.installer import InstallError, UninstallSummary
from cli_skills.settings import load_config, save_config
from cli_skills.targets import PiTarget


def make_catalog(skills):
    """@brief Build a manifest catalog fixture with skill entries only."""
    return {"skills": list(skills)}


class RemoveSkillTests(unittest.TestCase):
    """Level 1: `CliTarget.remove_skills` destination behavior."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        self.skills_dir = self.home / ".pi" / "agent" / "skills"
        self.skills_dir.mkdir(parents=True)
        self.target = PiTarget()

    def test_removes_managed_directory_and_preserves_siblings(self):
        """@brief Verify managed skill removal preserves sibling directories."""
        managed = self.skills_dir / "demo"
        managed.mkdir()
        (managed / "SKILL.md").write_text("demo", encoding="utf-8")
        sibling = self.skills_dir / "keep"
        sibling.mkdir()
        removed = self.target.remove_skills(["demo"], home=self.home)
        self.assertEqual(removed, 1)
        self.assertFalse(managed.exists())
        self.assertTrue(sibling.is_dir())

    def test_missing_destination_counts_as_removed(self):
        """@brief Verify a missing destination skill counts as removed."""
        removed = self.target.remove_skills(["ghost"], home=self.home)
        self.assertEqual(removed, 1)
        self.assertFalse((self.skills_dir / "ghost").exists())


class UninstallTargetTests(unittest.TestCase):
    """Level 2: `uninstall_target` removes manifest skills."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.resources = self.root / "resources"
        skill = self.resources / "skills" / "demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("demo", encoding="utf-8")
        self.home = self.root / "home"
        destination_skills = self.home / ".pi" / "agent" / "skills"
        installed = destination_skills / "demo"
        installed.mkdir(parents=True)
        (installed / "SKILL.md").write_text("installed", encoding="utf-8")
        (destination_skills / "keep").mkdir()

    def test_removes_manifest_skills_and_preserves_siblings(self):
        """@brief Verify manifest skill removal preserves unmanaged directories."""
        catalog = make_catalog([{"file": "skills/demo/SKILL.md"}])
        summary = installer.uninstall_target(
            PiTarget(), catalog, resources_root=self.resources, home=self.home
        )
        self.assertEqual(summary.cli, "pi")
        self.assertEqual(summary.skills, 1)
        self.assertFalse((self.home / ".pi" / "agent" / "skills" / "demo").exists())
        self.assertTrue((self.home / ".pi" / "agent" / "skills" / "keep").is_dir())

    def test_missing_manifest_source_fails_target(self):
        """@brief Verify a missing manifest source raises InstallError."""
        catalog = make_catalog([{"file": "skills/ghost/SKILL.md"}])
        with self.assertRaises(InstallError):
            installer.uninstall_target(
                PiTarget(), catalog, resources_root=self.resources, home=self.home
            )


class UninstallEnabledTests(unittest.TestCase):
    """Level 3: `uninstall_enabled` orchestration over the enabled configuration."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)

    def test_no_enabled_cli_returns_empty(self):
        """@brief Verify an empty enabled set returns no summaries or errors."""
        summaries, errors = installer.uninstall_enabled(home=self.home)
        self.assertEqual((summaries, errors), ([], []))

    def test_uninstalls_enabled_cli(self):
        """@brief Verify each enabled CLI is processed once with the home override."""
        save_config({"enabled": ["pi"]}, self.home)
        summary = UninstallSummary(cli="pi", skills=2)
        with patch.object(installer, "build_catalog", return_value=make_catalog([])), patch.object(
            installer, "uninstall_target", return_value=summary
        ) as uninstall:
            summaries, errors = installer.uninstall_enabled(home=self.home)
        self.assertEqual(summaries, [summary])
        self.assertEqual(errors, [])
        self.assertEqual(uninstall.call_args.args[1], make_catalog([]))
        self.assertEqual(uninstall.call_args.kwargs["home"], self.home)

    def test_continues_after_one_cli_failure(self):
        """@brief Verify one CLI failure does not stop remaining CLIs."""
        save_config({"enabled": ["pi", "claude"]}, self.home)
        summary = UninstallSummary(cli="claude", skills=1)
        outcomes = [OSError("boom"), summary]
        with patch.object(installer, "build_catalog", return_value=make_catalog([])), patch.object(
            installer, "uninstall_target", side_effect=outcomes
        ):
            summaries, errors = installer.uninstall_enabled(home=self.home)
        self.assertEqual(summaries, [summary])
        self.assertEqual(errors, ["pi: boom"])
        self.assertEqual(load_config(self.home)["enabled"], ["pi", "claude"])


class UninstallCliTests(unittest.TestCase):
    """Level 4: CLI dispatch of the `uninstall` command."""

    def run_uninstall(self, result):
        with patch.object(core, "check_version"), patch.object(
            core, "uninstall_enabled", return_value=result
        ), contextlib.redirect_stdout(io.StringIO()) as output:
            code = core.main(["uninstall"])
        return code, output.getvalue()

    def test_dispatch_prints_removed_counts(self):
        """@brief Verify the per-CLI removed skill count is printed."""
        code, output = self.run_uninstall(([UninstallSummary(cli="pi", skills=2)], []))
        self.assertEqual(code, 0)
        self.assertIn("Removed 2 skills for pi.", output)

    def test_no_enabled_cli_prints_informational_message(self):
        """@brief Verify the no-enabled-CLI informational message and exit code."""
        code, output = self.run_uninstall(([], []))
        self.assertEqual(code, 0)
        self.assertIn("No CLI enabled.", output)

    def test_failure_reports_error_and_exit_code_one(self):
        """@brief Verify a collected failure prints an error and exits 1."""
        with patch.object(core, "check_version"), patch.object(
            core, "uninstall_enabled", return_value=([], ["pi: boom"])
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            code = core.main(["uninstall"])
        self.assertEqual(code, 1)
        self.assertIn("Error: pi: boom", err.getvalue())

    def test_help_and_command_specific_help_list_uninstall(self):
        """@brief Verify the help screens list the skills-only uninstall command."""
        self.assertIn("uninstall", core.HELP)
        with patch.object(core, "check_version"), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(core.main(["uninstall", "--help"]), 0)
        self.assertEqual(
            output.getvalue(),
            "uninstall - Remove installed skills for every enabled CLI.\n",
        )


if __name__ == "__main__":
    unittest.main()
