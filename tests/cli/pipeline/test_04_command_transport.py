import json
import shutil

import pytest
from pydantic import JsonValue, TypeAdapter

from modwire.application import FileId, ImportIdentity, SourceFile, SourceParseError

from ..base_test import CliTestCase


class TestExtractorCommandTransport(CliTestCase):
    def copy_sources(self) -> None:
        shutil.copytree(
            self.repository / "tests/fixtures/command_transport/python/valid", self.workspace, dirs_exist_ok=True
        )

    def source_file(self, source_id: FileId, document: dict[str, JsonValue]) -> SourceFile:
        return SourceFile.model_validate(
            {**document, "file_id": source_id, "import_identity": ImportIdentity("example")}
        )

    @pytest.mark.parametrize("payload", ([], {"example_identity": 42}, None))
    def test_invalid_batch_payload_returns_failure_without_source_output(self, payload: object) -> None:
        completed = self.run_python_batch_extractor(self.workspace, json.dumps(payload))

        assert completed.returncode == 1
        assert completed.stdout == ""
        assert "Expected a JSON object mapping source ids to Python file paths." in completed.stderr

    def test_native_failure_after_a_valid_record_rejects_the_batch_and_recovers(self) -> None:
        self.copy_sources()
        invalid = self.workspace / "example_invalid.py"
        shutil.copyfile(self.repository / "tests/fixtures/command_transport/python/invalid/example_invalid.py", invalid)
        completed = self.run_python_batch_extractor(
            self.workspace,
            json.dumps({"example_identity": str(self.workspace / "example.py"), "example_invalid": str(invalid)}),
        )

        assert completed.returncode == 1
        record = TypeAdapter(tuple[FileId, dict[str, JsonValue]]).validate_json(completed.stdout)
        assert record[0] == FileId("example_identity")
        assert "modwire-error:" in completed.stderr
        with pytest.raises(SourceParseError) as raised:
            self.application.generate_map("python", str(self.workspace), self.scan_policy())
        assert raised.value.path.endswith("example_invalid.py")
        invalid.unlink()
        recovered = self.application.generate_map("python", str(self.workspace), self.scan_policy())
        assert tuple(recovered.extraction.files) == ("example.py", "example_second.py")

    def test_empty_batch_returns_no_records(self) -> None:
        completed = self.run_python_batch_extractor(self.workspace, "{}")

        assert completed.returncode == 0, completed.stderr
        assert completed.stdout == ""

    def test_batch_command_preserves_supplied_source_identities(self) -> None:
        self.copy_sources()
        completed = self.run_python_batch_extractor(
            self.workspace,
            json.dumps(
                {
                    "example_first_identity": str(self.workspace / "example.py"),
                    "example_second_identity": str(self.workspace / "example_second.py"),
                }
            ),
        )

        assert completed.returncode == 0, completed.stderr
        adapter = TypeAdapter(tuple[FileId, dict[str, JsonValue]])
        records = tuple(adapter.validate_json(line) for line in completed.stdout.splitlines())
        assert tuple(source_id for source_id, _ in records) == (
            FileId("example_first_identity"),
            FileId("example_second_identity"),
        )
        sources = tuple(self.source_file(source_id, document) for source_id, document in records)
        assert tuple(source.declarations[0].name for source in sources) == ("ExampleValue", "ExampleOther")

    def test_single_source_command_returns_one_source_document(self) -> None:
        self.copy_sources()
        completed = self.run_python_single_extractor(self.workspace, self.workspace / "example.py")

        assert completed.returncode == 0, completed.stderr
        document = TypeAdapter(dict[str, JsonValue]).validate_json(completed.stdout)
        source = self.source_file(FileId("example.py"), document)
        assert source.declarations[0].name == "ExampleValue"
        assert "example.py" not in document
