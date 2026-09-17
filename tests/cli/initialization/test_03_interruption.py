from ..base_test import CliTestCase


class TestInitializationInterruption(CliTestCase):
    def test_preserves_existing_configuration(self) -> None:
        self.write_files({".modwire/architecture.yaml": "example_custom: true\n"})
        result = self.run_cli(("init",))
        assert result.returncode == 0, result.stderr
        assert "Preserved .modwire/architecture.yaml." in result.stdout
        assert (self.workspace / ".modwire/architecture.yaml").read_text() == "example_custom: true\n"
