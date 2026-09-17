from ..base_test import CliTestCase


class TestReportCommands(CliTestCase):
    def test_explicit_and_legacy_commands_preserve_exit_status_and_output(self) -> None:
        self.write_project(1)
        explicit = self.run_cli(("report", "--language", "python"))
        legacy = self.run_cli(("--language", "python"))
        assert explicit.returncode == legacy.returncode == 0
        assert explicit.stdout == legacy.stdout
        assert "Architecture checks passed." in explicit.stdout

    def test_summary_omits_file_listing(self) -> None:
        self.write_project(1)
        result = self.run_cli(("report", "--language", "python", "--summary"))
        assert result.returncode == 0, result.stderr
        assert "Architecture checks passed." in result.stdout
        assert "src/example.py" not in result.stdout

    def test_violation_sets_a_nonzero_exit_status(self) -> None:
        self.write_project(0)
        result = self.run_cli(("report", "--language", "python", "--summary"))
        assert result.returncode == 1
        assert "max_functions_per_file" in result.stdout
        assert "src/example.py" in result.stdout
