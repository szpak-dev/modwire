from ..base_test import CliTestCase


class TestInitializationRecovery(CliTestCase):
    def test_force_restores_guidance(self) -> None:
        self.write_files({"AGENTS.md": "example_custom\n"})
        result = self.run_cli(("init", "--force"))
        assert result.returncode == 0, result.stderr
        assert "Overwritten AGENTS.md." in result.stdout
        assert (self.workspace / "AGENTS.md").read_text() == "Check `.modwire/INDEX.md` before making changes.\n"
