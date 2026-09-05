from ..base_test import CliTestCase


class TestInitializationCleanup(CliTestCase):
    def test_force_replaces_configuration(self) -> None:
        self.write_files({".modwire/architecture.yaml": "example_custom: true\n"})
        result = self.run_cli(("init", "--force"))
        assert result.returncode == 0, result.stderr
        assert "Overwritten .modwire/architecture.yaml." in result.stdout
        assert self.application.load_configuration(self.workspace / ".modwire").shape.realms
