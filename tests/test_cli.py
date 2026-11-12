import contextlib
from email.message import Message
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from cli_skills import core


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "cache.json"
        patcher = patch.object(core, "cache_path", return_value=self.path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.err = io.StringIO()
        self.redirect = contextlib.redirect_stderr(self.err)
        self.redirect.__enter__()
        self.addCleanup(self.redirect.__exit__, None, None, None)

    def release(self, tag):
        return io.BytesIO(json.dumps({"tag_name": tag}).encode())

    def pypi_release(self, version):
        return io.BytesIO(json.dumps({"info": {"version": version}}).encode())

    @patch("cli_skills.core.time.time", return_value=1000)
    def test_new_version_and_cached_check(self, clock):
        with patch("cli_skills.core.urlopen", return_value=self.pypi_release("1.2.3")) as request:
            core.check_version()
            core.check_version()
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args.kwargs["timeout"], 2)
        self.assertIn("pypi.org/pypi/cli-skills/json", request.call_args.args[0].full_url)
        data = json.loads(self.path.read_text())
        self.assertEqual(data["last_success_epoch"], 1000)
        self.assertEqual(data["idle_time_epoch"], 4600)
        self.assertIn("\x1b[92m", self.err.getvalue())

    @patch("cli_skills.core.time.time", return_value=1000)
    def test_failure_preserves_success_and_backs_off(self, clock):
        self.path.write_text(json.dumps({"last_success_epoch": 500, "idle_time_epoch": 999}))
        error = HTTPError(core.ENDPOINT, 429, "Too Many Requests", Message(), None)
        with patch("cli_skills.core.urlopen", side_effect=error):
            core.check_version()
        data = json.loads(self.path.read_text())
        self.assertEqual(data["last_success_epoch"], 500)
        self.assertEqual(data["idle_time_epoch"], 87400)
        self.assertIn("429", self.err.getvalue())
        self.assertIn("\x1b[91m", self.err.getvalue())

    @patch("cli_skills.core.time.time", return_value=1000)
    def test_no_newer_release_is_negative(self, clock):
        with patch("cli_skills.core.urlopen", return_value=self.pypi_release("0.0.0")):
            core.check_version()
        data = json.loads(self.path.read_text())
        self.assertEqual(data["last_success_epoch"], 1000)
        self.assertEqual(data["idle_time_epoch"], 87400)

    def test_version_forces_check_and_help_output(self):
        """
        @brief Verify the `--version` report lines and the forced release check.
        @details Patches the fetchers with fixed versions; expects exit code 0,
                 the exact aligned three-line report, and one `check_version`
                 call with `force=True`.
        @expected_output `Current Installed : <installed>`, `Latest @ PyPI     : 9.9.9`,
                 and `Latest @ GitHub   : 8.8.8` lines.
        @satisfies REQ-005 REQ-006 REQ-060 REQ-061 REQ-070
        """
        with patch.object(core, "check_version") as check, patch.object(core, "fetch_pypi_latest", return_value="9.9.9"), patch.object(core, "fetch_github_latest", return_value="8.8.8"), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(core.main(["--version"]), 0)
            self.assertEqual(
                output.getvalue(),
                "Current Installed : "
                + core.__version__
                + "\nLatest @ PyPI     : 9.9.9\nLatest @ GitHub   : 8.8.8\n",
            )
            check.assert_called_once_with(force=True)
        with patch.object(core, "check_version"), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(core.main([]), 0)
            self.assertEqual(output.getvalue(), core.HELP + "\n")

    def test_management_platforms(self):
        with patch.object(core, "check_version"), patch.object(core, "load_config", return_value={"enabled": []}), patch.object(core.sys, "platform", "linux"), patch.object(core.subprocess, "run") as run:
            run.return_value.returncode = 0
            self.assertEqual(core.main(["--upgrade"]), 0)
            run.assert_called_once_with(core.UPGRADE, check=False)
        with patch.object(core, "check_version"), patch.object(core.sys, "platform", "darwin"), patch.object(core.subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(core.main(["--uninstall"]), 0)
            run.assert_not_called()
            self.assertIn("uv tool uninstall cli-skills", output.getvalue())

    @patch.object(core, "_post_upgrade_install", return_value=7)
    def test_upgrade_develop_installs_from_github(self, chained):
        """
        @brief Verify `--upgrade --dev` installs the latest GitHub release.
        @details Patches the platform to Linux, the latest-release lookup, and
                 the chained install; expects both `--upgrade --dev` and
                 `--develop --upgrade` argument orders to execute the
                 release-tag-pinned GitHub source and to chain the
                 post-upgrade install, returning its exit code.
        @param chained {MagicMock} Replacement for `_post_upgrade_install`.
        @return {None}
        @expected_output Exit code 7 from the chained install and
                 `subprocess.run` called with the pinned GitHub source.
        @satisfies REQ-063 REQ-062 REQ-043 REQ-046
        """
        with patch.object(core, "check_version"), patch.object(core.sys, "platform", "linux"), patch.object(core, "_latest_release_ref", return_value="v9.9.9"), patch.object(core.subprocess, "run") as run:
            run.return_value.returncode = 0
            self.assertEqual(core.main(["--upgrade", "--dev"]), 7)
            self.assertEqual(core.main(["--upgrade", "--develop"]), 7)
        self.assertEqual(run.call_args.args[0], core.UPGRADE_DEVELOP[:-1] + [core.GITHUB_GIT_URL + "@v9.9.9"])
        chained.assert_called_with()

    @patch.object(core, "_post_upgrade_install", return_value=7)
    def test_upgrade_force_reinstalls_from_pypi(self, chained):
        """
        @brief Verify `--upgrade --force` forces download and reinstallation.
        @details Patches the platform to Linux and the chained install; expects
                 `--upgrade --force` to execute `UPGRADE_FORCE` with the
                 reinstallation options and to chain the post-upgrade install,
                 returning its exit code.
        @param chained {MagicMock} Replacement for `_post_upgrade_install`.
        @return {None}
        @expected_output Exit code 7 from the chained install and
                 `subprocess.run` called with `UPGRADE_FORCE`.
        @satisfies REQ-067 REQ-043 REQ-046
        """
        with patch.object(core, "check_version"), patch.object(core.sys, "platform", "linux"), patch.object(core.subprocess, "run") as run:
            run.return_value.returncode = 0
            self.assertEqual(core.main(["--upgrade", "--force"]), 7)
        self.assertEqual(run.call_args.args[0], core.UPGRADE_FORCE)
        chained.assert_called_with()

    @patch.object(core, "_post_upgrade_install", return_value=7)
    def test_upgrade_develop_force_reinstalls_from_github(self, chained):
        """
        @brief Verify forced `--upgrade --dev` reinstalls the GitHub release.
        @details Patches the platform to Linux, the latest-release lookup, and
                 the chained install; expects every accepted option order of
                 `--dev`/`--develop` combined with `--force` to execute the
                 release-tag-pinned forced GitHub source and to chain the
                 post-upgrade install, returning its exit code.
        @param chained {MagicMock} Replacement for `_post_upgrade_install`.
        @return {None}
        @expected_output Exit code 7 from the chained install and
                 `subprocess.run` called with the pinned forced GitHub source.
        @satisfies REQ-068 REQ-062 REQ-043 REQ-046
        """
        with patch.object(core, "check_version"), patch.object(core.sys, "platform", "linux"), patch.object(core, "_latest_release_ref", return_value="v9.9.9"), patch.object(core.subprocess, "run") as run:
            run.return_value.returncode = 0
            self.assertEqual(core.main(["--upgrade", "--dev", "--force"]), 7)
            self.assertEqual(core.main(["--upgrade", "--force", "--develop"]), 7)
        self.assertEqual(run.call_args.args[0], core.UPGRADE_DEVELOP_FORCE[:-1] + [core.GITHUB_GIT_URL + "@v9.9.9"])
        chained.assert_called_with()

    @patch.object(core, "_post_upgrade_install", return_value=7)
    def test_upgrade_develop_pins_latest_github_release_tag(self, chained):
        """
        @brief Verify `--upgrade --dev` downloads the latest GitHub release tag.
        @details Patches the platform to Linux, the latest-release lookup, and
                 the chained install; expects the uv git source to pin the
                 resolved release tag so a default branch behind the latest
                 release cannot be installed instead.
        @param chained {MagicMock} Replacement for `_post_upgrade_install`.
        @return {None}
        @expected_output Exit code 7 from the chained install and
                 `subprocess.run` called with the release-tag-pinned source.
        @satisfies REQ-062 REQ-063 DES-082 DES-083
        """
        with patch.object(core, "check_version"), patch.object(core.sys, "platform", "linux"), patch.object(core, "_latest_release_ref", return_value="v9.9.9"), patch.object(core.subprocess, "run") as run:
            run.return_value.returncode = 0
            self.assertEqual(core.main(["--upgrade", "--dev"]), 7)
        self.assertEqual(run.call_args.args[0], ["uv", "tool", "install", "cli-skills", "--from", core.GITHUB_GIT_URL + "@v9.9.9"])
        chained.assert_called_with()

    @patch.object(core, "_post_upgrade_install", return_value=7)
    def test_upgrade_develop_falls_back_when_release_lookup_fails(self, chained):
        """
        @brief Verify `--upgrade --dev` keeps the unpinned source on lookup failure.
        @details Patches the latest-release lookup to fail and expects the
                 unpinned GitHub source to be executed with a stderr warning.
        @param chained {MagicMock} Replacement for `_post_upgrade_install`.
        @return {None}
        @expected_output Exit code 7, `subprocess.run` called with
                 `UPGRADE_DEVELOP`, and a warning on stderr.
        @satisfies REQ-063 DES-082 REQ-066
        """
        with patch.object(core, "check_version"), patch.object(core.sys, "platform", "linux"), patch.object(core, "_github_tag", side_effect=OSError("lookup failed")), patch.object(core.subprocess, "run") as run:
            run.return_value.returncode = 0
            self.assertEqual(core.main(["--upgrade", "--dev"]), 7)
        self.assertEqual(run.call_args.args[0], core.UPGRADE_DEVELOP)
        self.assertIn("Warning", self.err.getvalue())
        chained.assert_called_with()

    def test_upgrade_force_prints_manual_command_on_non_linux(self):
        """
        @brief Verify `--upgrade --force` prints the forced manual command off Linux.
        @details Patches the platform to darwin; expects exit code 0 without
                 spawning a child process and a manual command carrying the
                 reinstallation options.
        @return {None}
        @expected_output Exit code 0, `subprocess.run` not called, and the
                 forced uv command printed to stdout.
        @satisfies REQ-069 REQ-011 REQ-012
        """
        with patch.object(core, "check_version"), patch.object(core.sys, "platform", "darwin"), patch.object(core.subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(core.main(["--upgrade", "--force"]), 0)
            run.assert_not_called()
            self.assertIn("uv tool install cli-skills --force --reinstall --refresh", output.getvalue())

    def test_force_without_upgrade_is_usage_error(self):
        """
        @brief Verify `--force` without `--upgrade` is a usage error.
        @details Patches the release check; expects exit code 2 for `--force`
                 invoked alone and when preceding `--upgrade`.
        @return {None}
        @expected_output Exit code 2 for `--force` alone and before `--upgrade`.
        @satisfies REQ-064 REQ-065
        """
        with patch.object(core, "check_version"), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(core.main(["--force"]), 2)
            self.assertEqual(core.main(["--force", "--upgrade"]), 2)

    def test_invalid_upgrade_option_combinations_are_usage_error(self):
        """
        @brief Verify invalid `--upgrade` option combinations are usage errors.
        @details Patches the release check; expects exit code 2 for duplicate
                 options, the redundant `--dev` plus `--develop` combination,
                 and unknown options following `--upgrade`.
        @return {None}
        @expected_output Exit code 2 for every invalid option combination.
        @satisfies REQ-065
        """
        with patch.object(core, "check_version"), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(core.main(["--upgrade", "--dev", "--develop"]), 2)
            self.assertEqual(core.main(["--upgrade", "--force", "--force"]), 2)
            self.assertEqual(core.main(["--upgrade", "--bogus"]), 2)

    def test_develop_without_upgrade_is_usage_error(self):
        """
        @brief Verify `--dev`/`--develop` without `--upgrade` is a usage error.
        @details Patches the release check; expects exit code 2 for both
                 spellings invoked alone.
        @return {None}
        @expected_output Exit code 2 for `--dev` and `--develop` alone.
        @satisfies REQ-064
        """
        with patch.object(core, "check_version"), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(core.main(["--dev"]), 2)
            self.assertEqual(core.main(["--develop"]), 2)

    def test_legacy_argument_orders_are_rejected(self):
        """
        @brief Verify legacy argument orders are rejected as usage errors.
        @details Asserts exit code 2 for `--help` preceding a command name and
                 for `--dev`/`--develop` preceding `--upgrade`; only the
                 canonical `<command> --help` and `--upgrade --dev` forms
                 dispatch.
        @return {None}
        @expected_output Exit code 2 for every legacy argument order.
        @satisfies REQ-065
        """
        with patch.object(core, "check_version"), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(core.main(["--help", "show"]), 2)
            self.assertEqual(core.main(["--dev", "--upgrade"]), 2)
            self.assertEqual(core.main(["--develop", "--upgrade"]), 2)


if __name__ == "__main__":
    unittest.main()
