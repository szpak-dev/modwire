from ..base_test import CliTestCase


class TestInitializationAttacks(CliTestCase):
    def test_rejects_directory_escape(self) -> None:
        result = self.run_cli(("init", "--dot-dir", "../example_outside"))
        assert result.returncode == 1
        assert "Initialization target escapes the project" in result.stdout
        assert not (self.workspace.parent / "example_outside").exists()
