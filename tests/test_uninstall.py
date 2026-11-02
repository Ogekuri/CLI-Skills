"""Uninstall command unit tests: adapter removal, target uninstallation, enabled orchestration, and CLI dispatch."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skills import core, installer
from skills.installer import InstallError, UninstallSummary
from skills.settings import load_config, save_config
from skills.targets import OpenClawTarget, PiTarget


def make_catalog(skills, prompts):
    return {"skills": list(skills), "prompts": list(prompts)}


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
        removed = self.target.remove_skills(["ghost"], home=self.home)
        self.assertEqual(removed, 1)
        self.assertFalse((self.skills_dir / "ghost").exists())


class RemovePromptTests(unittest.TestCase):
    """Level 1: `CliTarget.remove_prompts` destination behavior."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        self.prompts_dir = self.home / ".pi" / "agent" / "prompts"
        self.prompts_dir.mkdir(parents=True)
        self.target = PiTarget()

    def test_removes_managed_prompts_and_preserves_unmanaged(self):
        (self.prompts_dir / "greet.md").write_text("a", encoding="utf-8")
        (self.prompts_dir / "stale.md").write_text("b", encoding="utf-8")
        (self.prompts_dir / "unrelated.md").write_text("c", encoding="utf-8")
        removed = self.target.remove_prompts(["greet.md", "stale.md"], home=self.home)
        self.assertEqual(removed, 2)
        self.assertFalse((self.prompts_dir / "greet.md").exists())
        self.assertFalse((self.prompts_dir / "stale.md").exists())
        self.assertTrue((self.prompts_dir / "unrelated.md").is_file())

    def test_unsupported_prompts_destination_returns_zero(self):
        unsupported = OpenClawTarget()
        self.assertEqual(unsupported.remove_prompts(["x.md"], home=self.home), 0)

    def test_unsafe_names_are_skipped(self):
        removed = self.target.remove_prompts(["../evil.md", "", ".", ".."], home=self.home)
        self.assertEqual(removed, 0)


class UninstallTargetTests(unittest.TestCase):
    """Level 2: `uninstall_target` removes manifest skills and union prompts."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.resources = self.root / "resources"
        skill = self.resources / "skills" / "demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("demo", encoding="utf-8")
        prompts = self.resources / "prompts"
        prompts.mkdir(parents=True)
        (prompts / "greet.md").write_text("hi", encoding="utf-8")
        self.home = self.root / "home"
        destination_skills = self.home / ".pi" / "agent" / "skills"
        installed = destination_skills / "demo"
        installed.mkdir(parents=True)
        (installed / "SKILL.md").write_text("installed", encoding="utf-8")
        (destination_skills / "keep").mkdir()
        destination_prompts = self.home / ".pi" / "agent" / "prompts"
        destination_prompts.mkdir(parents=True)
        (destination_prompts / "greet.md").write_text("old", encoding="utf-8")
        (destination_prompts / "stale.md").write_text("stale", encoding="utf-8")
        (destination_prompts / "unrelated.md").write_text("keep", encoding="utf-8")

    def test_removes_manifest_skills_and_union_prompts(self):
        catalog = make_catalog([{"file": "skills/demo/SKILL.md"}], [{"file": "prompts/greet.md"}])
        summary = installer.uninstall_target(
            PiTarget(), catalog, ["stale.md"], resources_root=self.resources, home=self.home
        )
        self.assertEqual(summary.cli, "pi")
        self.assertEqual(summary.skills, 1)
        self.assertEqual(summary.prompts, 2)
        self.assertFalse((self.home / ".pi" / "agent" / "skills" / "demo").exists())
        self.assertTrue((self.home / ".pi" / "agent" / "skills" / "keep").is_dir())
        self.assertFalse((self.home / ".pi" / "agent" / "prompts" / "greet.md").exists())
        self.assertFalse((self.home / ".pi" / "agent" / "prompts" / "stale.md").exists())
        self.assertTrue((self.home / ".pi" / "agent" / "prompts" / "unrelated.md").is_file())

    def test_missing_manifest_source_fails_target(self):
        catalog = make_catalog([{"file": "skills/ghost/SKILL.md"}], [])
        with self.assertRaises(InstallError):
            installer.uninstall_target(
                PiTarget(), catalog, [], resources_root=self.resources, home=self.home
            )


class UninstallEnabledTests(unittest.TestCase):
    """Level 3: `uninstall_enabled` orchestration over the enabled configuration."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)

    def test_no_enabled_cli_returns_empty(self):
        summaries, errors = installer.uninstall_enabled(home=self.home)
        self.assertEqual((summaries, errors), ([], []))

    def test_uninstalls_enabled_cli_and_clears_prompt_records(self):
        save_config({"enabled": ["pi"], "prompts": {"pi": ["greet.md"]}}, self.home)
        summary = UninstallSummary(cli="pi", skills=2, prompts=1)
        with patch.object(installer, "build_catalog", return_value=make_catalog([], [])), patch.object(
            installer, "uninstall_target", return_value=summary
        ) as uninstall:
            summaries, errors = installer.uninstall_enabled(home=self.home)
        self.assertEqual(summaries, [summary])
        self.assertEqual(errors, [])
        self.assertEqual(uninstall.call_args.args[2], ["greet.md"])
        self.assertEqual(uninstall.call_args.kwargs["home"], self.home)
        self.assertEqual(load_config(self.home)["prompts"]["pi"], [])

    def test_continues_after_one_cli_failure(self):
        save_config(
            {"enabled": ["pi", "claude"], "prompts": {"pi": ["greet.md"], "claude": ["old.md"]}},
            self.home,
        )
        summary = UninstallSummary(cli="claude", skills=1, prompts=1)
        outcomes = [OSError("boom"), summary]
        with patch.object(installer, "build_catalog", return_value=make_catalog([], [])), patch.object(
            installer, "uninstall_target", side_effect=outcomes
        ):
            summaries, errors = installer.uninstall_enabled(home=self.home)
        self.assertEqual(summaries, [summary])
        self.assertEqual(errors, ["pi: boom"])
        config = load_config(self.home)
        self.assertEqual(config["prompts"]["pi"], ["greet.md"])
        self.assertEqual(config["prompts"]["claude"], [])


class UninstallCliTests(unittest.TestCase):
    """Level 4: CLI dispatch of the `uninstall` command."""

    def run_uninstall(self, result):
        with patch.object(core, "check_version"), patch.object(
            core, "uninstall_enabled", return_value=result
        ), contextlib.redirect_stdout(io.StringIO()) as output:
            code = core.main(["uninstall"])
        return code, output.getvalue()

    def test_dispatch_prints_removed_counts(self):
        code, output = self.run_uninstall(([UninstallSummary(cli="pi", skills=2, prompts=1)], []))
        self.assertEqual(code, 0)
        self.assertIn("Removed 2 skills and 1 prompts for pi.", output)

    def test_no_enabled_cli_prints_informational_message(self):
        code, output = self.run_uninstall(([], []))
        self.assertEqual(code, 0)
        self.assertIn("No CLI enabled.", output)

    def test_failure_reports_error_and_exit_code_one(self):
        with patch.object(core, "check_version"), patch.object(
            core, "uninstall_enabled", return_value=([], ["pi: boom"])
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            code = core.main(["uninstall"])
        self.assertEqual(code, 1)
        self.assertIn("Error: pi: boom", err.getvalue())

    def test_help_and_command_specific_help_list_uninstall(self):
        self.assertIn("uninstall", core.HELP)
        with patch.object(core, "check_version"), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(core.main(["uninstall", "--help"]), 0)
        self.assertEqual(
            output.getvalue(),
            "uninstall - Remove installed skills and prompts for every enabled CLI.\n",
        )


if __name__ == "__main__":
    unittest.main()
