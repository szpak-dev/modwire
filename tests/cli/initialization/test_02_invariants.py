from ..base_test import CliTestCase


class TestInitializationInvariants(CliTestCase):
    def test_writes_valid_configuration_and_guidance(self) -> None:
        result = self.run_cli(("init",))
        assert result.returncode == 0, result.stderr
        config = self.application.load_configuration(self.workspace / ".modwire")
        assert config.boundaries.tags[0].name == "module"
        assert config.shape.realms[0].shape.max_functions_per_file == 1
        assert config.shape.realms[0].shape.max_variables_per_file == 0
        assert (self.workspace / "AGENTS.md").read_text() == "Check `.modwire/INDEX.md` before making changes.\n"
        index = (self.workspace / ".modwire/INDEX.md").read_text()
        for name in ("ARCHITECTURE.md", "MODWIRE.md", "RULES.md", "TESTING.md", "WORKFLOW.md"):
            assert f"docs/{name}" in index
            assert (self.workspace / ".modwire/docs" / name).is_file()
