import json

import pytest

from ..base_test import CliTestCase


class TestExtractorCommandTransport(CliTestCase):
    def test_batch_command_preserves_supplied_source_identities(self) -> None:
        self.write_files({"example.py": "class ExampleValue: pass\n"})
        completed = self.run_python_batch_extractor(
            self.workspace,
            json.dumps({"example_identity": str(self.workspace / "example.py")}),
        )

        assert completed.returncode == 0, completed.stderr
        result = json.loads(completed.stdout)
        assert tuple(result) == ("example_identity",)
        assert result["example_identity"]["classes"][0]["name"] == "ExampleValue"

    def test_single_source_command_returns_one_source_document(self) -> None:
        self.write_files({"example.py": "class ExampleValue: pass\n"})
        completed = self.run_python_single_extractor(self.workspace, self.workspace / "example.py")

        assert completed.returncode == 0, completed.stderr
        result = json.loads(completed.stdout)
        assert result["classes"][0]["name"] == "ExampleValue"
        assert "example.py" not in result

    @pytest.mark.parametrize("payload", ([], {"example_identity": 42}, None))
    def test_invalid_batch_payload_returns_failure_without_source_output(self, payload: object) -> None:
        completed = self.run_python_batch_extractor(self.workspace, json.dumps(payload))

        assert completed.returncode == 1
        assert completed.stdout == ""
        assert "Expected a JSON object mapping source ids to Python file paths." in completed.stderr

    def test_empty_batch_returns_an_empty_document(self) -> None:
        completed = self.run_python_batch_extractor(self.workspace, "{}")

        assert completed.returncode == 0, completed.stderr
        assert json.loads(completed.stdout) == {}
