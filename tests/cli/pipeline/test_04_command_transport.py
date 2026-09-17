import json
import sys
from io import StringIO

import pytest

from ..base_test import CliTestCase


class TestExtractorCommandTransport(CliTestCase):
    def test_batch_command_preserves_supplied_source_identities(self, monkeypatch, capsys) -> None:
        self.write_files({"example.py": "class ExampleValue: pass\n"})
        monkeypatch.setattr(sys, "argv", ["example-helper", "--batch", str(self.workspace)])
        monkeypatch.setattr(
            sys, "stdin", StringIO(json.dumps({"example_identity": str(self.workspace / "example.py")}))
        )
        assert self.application.run_extractor("python") == 0
        result = json.loads(capsys.readouterr().out)
        assert tuple(result) == ("example_identity",)
        assert result["example_identity"]["classes"][0]["name"] == "ExampleValue"

    def test_single_source_command_returns_one_source_document(self, monkeypatch, capsys) -> None:
        self.write_files({"example.py": "class ExampleValue: pass\n"})
        monkeypatch.setattr(sys, "argv", ["example-helper", str(self.workspace / "example.py"), str(self.workspace)])
        assert self.application.run_extractor("python") == 0
        result = json.loads(capsys.readouterr().out)
        assert result["classes"][0]["name"] == "ExampleValue"
        assert "example.py" not in result

    @pytest.mark.parametrize("payload", ([], {"example_identity": 42}, None))
    def test_invalid_batch_payload_returns_failure_without_source_output(
        self, payload: object, monkeypatch, capsys
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["example-helper", "--batch", str(self.workspace)])
        monkeypatch.setattr(sys, "stdin", StringIO(json.dumps(payload)))
        assert self.application.run_extractor("python") == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Expected a JSON object mapping source ids to Python file paths." in captured.err

    def test_empty_batch_returns_an_empty_document(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr(sys, "argv", ["example-helper", "--batch", str(self.workspace)])
        monkeypatch.setattr(sys, "stdin", StringIO("{}"))
        assert self.application.run_extractor("python") == 0
        assert json.loads(capsys.readouterr().out) == {}
