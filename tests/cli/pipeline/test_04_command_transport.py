import json
import os
import shutil
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from importlib import resources
from pathlib import Path

import pytest
from pydantic import JsonValue, TypeAdapter

from modwire.application import (
    ExtractorContractError,
    ExtractorContractViolation,
    FileId,
    ImportIdentity,
    SourceFile,
    SourceParseError,
)

from ..base_test import CliTestCase


class TestExtractorCommandTransport(CliTestCase):
    def run_java_batch(self, sources: dict[str, str]) -> subprocess.CompletedProcess[str]:
        runtime = self.application.extraction.request("java", str(self.workspace)).runtime
        entrypoint = runtime.entrypoint
        with resources.as_file(resources.files(entrypoint.package).joinpath(entrypoint.path)) as script:
            return subprocess.run(
                (*runtime.command, *entrypoint.command_arguments(script), "--batch", str(self.workspace)),
                input=json.dumps(sources),
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )

    def test_java_batch_keeps_requested_order_across_reused_workers(self) -> None:
        fixture = self.repository / "tests/fixtures/call_occurrences/java"
        sources = {
            "example_third": str(fixture / "ExampleMixedCalls.java"),
            "example_first": str(fixture / "ExampleCalls.java"),
            "example_fourth": str(fixture / "ExampleMixedCalls.java"),
            "example_second": str(fixture / "ExampleCalls.java"),
            "example_last": str(fixture / "ExampleMixedCalls.java"),
        }

        completed = self.run_java_batch(sources)

        assert completed.returncode == 0, completed.stderr
        records = [TypeAdapter(dict[str, JsonValue]).validate_json(line) for line in completed.stdout.splitlines()]
        assert [record["source_id"] for record in records] == list(sources)
        for record in records:
            texts = TypeAdapter(list[str]).validate_python(record["texts"])
            assert texts[0] == record["source_id"]

    @pytest.mark.parametrize("invalid_position", (0, 1, 2))
    def test_java_batch_reports_the_first_input_failure_in_order(self, invalid_position: int) -> None:
        valid = self.repository / "tests/fixtures/call_occurrences/java/ExampleCalls.java"
        invalid = self.repository / "tests/fixtures/code_map_reuse/native_failure/java/Broken.java"
        sources = {f"example_{index}": str(invalid if index == invalid_position else valid) for index in range(3)}

        completed = self.run_java_batch(sources)

        assert completed.returncode == 1
        records = [TypeAdapter(dict[str, JsonValue]).validate_json(line) for line in completed.stdout.splitlines()]
        assert [record["source_id"] for record in records] == list(sources)[:invalid_position]
        assert completed.stderr.startswith("modwire-error:")
        assert "Broken.java" in completed.stderr

    def test_java_empty_batch_returns_no_records(self) -> None:
        completed = self.run_java_batch({})

        assert completed.returncode == 0, completed.stderr
        assert completed.stdout == ""

    @contextmanager
    def altered_ruby_output(self, mode: str) -> Iterator[Path]:
        sources = self.workspace / "sources"
        fixtures = self.repository / "tests/fixtures/implementation_manifest/ruby"
        shutil.copytree(fixtures / "canonical/src", sources)
        shutil.copyfile(fixtures / "no_calls/src/example.rb", sources / "example_second.rb")
        runtime = self.workspace / "runtime"
        runtime.mkdir()
        shutil.copyfile(self.repository / "tests/fixtures/command_transport/runtime/ruby", runtime / "ruby")
        (runtime / "ruby").chmod(0o755)
        ruby = shutil.which("ruby")
        assert ruby is not None
        with pytest.MonkeyPatch.context() as environment:
            environment.setenv("EXAMPLE_RUBY", ruby)
            environment.setenv("EXAMPLE_OUTPUT", mode)
            environment.setenv("PATH", str(runtime) + os.pathsep + os.environ["PATH"])
            yield sources

    @pytest.mark.parametrize(
        "mode",
        (
            "negative",
            "boolean",
            "fractional",
            "out_of_range",
            "wrong_type",
            "invalid_value",
            "invalid_text",
            "missing_table",
        ),
    )
    def test_indexed_ruby_rejects_invalid_references_and_recovers(self, mode: str) -> None:
        with self.altered_ruby_output(mode) as sources:
            with pytest.raises(ExtractorContractError) as raised:
                self.application.generate_map("ruby", str(sources), self.scan_policy())

        assert raised.value.language == "ruby"
        assert raised.value.violation is ExtractorContractViolation.INVALID_OUTPUT
        recovered = self.application.generate_map("ruby", str(sources), self.scan_policy())
        assert tuple(recovered.extraction.files) == ("example.rb", "example_second.rb")

    def test_indexed_ruby_uses_a_separate_reference_table_for_each_file(self) -> None:
        with self.altered_ruby_output("unchanged") as sources:
            extracted = self.application.generate_map("ruby", str(sources), self.scan_policy())

        recovered = self.application.generate_map("ruby", str(sources), self.scan_policy())
        assert tuple(extracted.extraction.files) == ("example.rb", "example_second.rb")
        for source_id, source in extracted.extraction.files.items():
            assert source.model_dump_json(exclude_unset=True) == recovered.extraction.files[source_id].model_dump_json(
                exclude_unset=True
            )

    @contextmanager
    def altered_typescript_output(self, mode: str) -> Iterator[Path]:
        sources = self.workspace / "sources"
        shutil.copytree(self.repository / "tests/fixtures/implementation_manifest/typescript/canonical/src", sources)
        runtime = self.workspace / "runtime"
        shutil.copytree(self.repository / "tests/fixtures/command_transport/runtime", runtime)
        (runtime / "node").chmod(0o755)
        node = shutil.which("node")
        assert node is not None
        with pytest.MonkeyPatch.context() as environment:
            environment.setenv("EXAMPLE_NODE", node)
            environment.setenv("EXAMPLE_OUTPUT", mode)
            environment.setenv("PATH", str(runtime) + os.pathsep + os.environ["PATH"])
            yield sources

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

    @pytest.mark.parametrize(
        ("mode", "violation", "missing", "unexpected", "duplicates"),
        (
            ("duplicate", ExtractorContractViolation.DUPLICATE_SOURCE_IDENTITY, (), (), ("example.ts",)),
            ("missing", ExtractorContractViolation.SOURCE_SET_MISMATCH, ("example.ts",), (), ()),
            (
                "unexpected",
                ExtractorContractViolation.SOURCE_SET_MISMATCH,
                ("example.ts",),
                ("example_unexpected.ts",),
                (),
            ),
            ("invalid", ExtractorContractViolation.INVALID_OUTPUT, (), (), ()),
        ),
    )
    def test_invalid_output_rejects_the_batch_and_recovers(
        self,
        mode: str,
        violation: ExtractorContractViolation,
        missing: tuple[str, ...],
        unexpected: tuple[str, ...],
        duplicates: tuple[str, ...],
    ) -> None:
        with self.altered_typescript_output(mode) as sources:
            with pytest.raises(ExtractorContractError) as raised:
                self.application.generate_map("typescript", str(sources), self.scan_policy())

        assert raised.value.language == "typescript"
        assert raised.value.violation is violation
        assert raised.value.missing_source_ids == missing
        assert raised.value.unexpected_source_ids == unexpected
        assert raised.value.duplicate_source_ids == duplicates
        recovered = self.application.generate_map("typescript", str(sources), self.scan_policy())
        assert tuple(recovered.extraction.files) == ("example.ts",)

    def test_native_omitted_defaults_remain_distinct_from_explicit_defaults(self) -> None:
        with self.altered_typescript_output("defaults") as sources:
            source = self.application.generate_map("typescript", str(sources), self.scan_policy()).extraction.files[
                "example.ts"
            ]
        callables = source.canonical_callables()
        omitted = tuple(item for item in callables if "docstring" not in item.model_dump(exclude_unset=True))

        assert len(omitted) == 1
        assert len(callables) > 1
        assert omitted[0].docstring == ""
        copied = omitted[0].model_copy(update={"docstring": ""})
        assert copied.model_dump(exclude_unset=True)["docstring"] == ""
        assert "docstring" not in omitted[0].model_dump(exclude_unset=True)

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
