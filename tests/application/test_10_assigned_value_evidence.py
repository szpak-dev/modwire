import pytest

from modwire.application import CapabilityStatus, FactCapability, SourceAssignedValueKind

from .base_test import ApplicationTestCase


class TestAssignedValueEvidence(ApplicationTestCase):
    def test_python_manifest_publishes_ordered_assigned_value_evidence(self) -> None:
        root = self.project(
            {
                "src/example.py": (
                    "EXAMPLE_REFERENCE = 'example'\n\n"
                    "def example_factory() -> object:\n"
                    "    return object()\n\n"
                    "class ExampleValue:\n"
                    "    example_unassigned: str\n"
                    "    example_literal = 1\n"
                    "    example_reference: str = EXAMPLE_REFERENCE\n"
                    "    example_call = example_factory()\n"
                    "    example_unresolved = 1 + 2\n\n"
                    "    def __init__(self, example_input: str):\n"
                    "        self.example_reference = example_input\n"
                    "        if example_input:\n"
                    "            self.example_nested = 1\n"
                    "        self.example_nested = 2\n"
                )
            }
        )
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map("python", root, self.scan_policy()), format
            )
        )
        owner_id = next(item.id for item in manifest.symbols if item.id.qualified_name == "ExampleValue")
        evidence = {
            item.name: tuple((value.kind, value.expression, value.reference) for value in item.assigned_values)
            for item in manifest.attributes
            if item.owner_symbol_id == owner_id
        }

        assert evidence == {
            "example_unassigned": ((SourceAssignedValueKind.UNASSIGNED, "", ""),),
            "example_literal": ((SourceAssignedValueKind.LITERAL, "1", ""),),
            "example_reference": (
                (SourceAssignedValueKind.REFERENCE, "EXAMPLE_REFERENCE", "EXAMPLE_REFERENCE"),
                (SourceAssignedValueKind.REFERENCE, "example_input", "example_input"),
            ),
            "example_call": ((SourceAssignedValueKind.CALL, "example_factory()", "example_factory"),),
            "example_unresolved": ((SourceAssignedValueKind.UNRESOLVED, "1 + 2", ""),),
            "example_nested": (
                (SourceAssignedValueKind.LITERAL, "1", ""),
                (SourceAssignedValueKind.LITERAL, "2", ""),
            ),
        }

    @pytest.mark.parametrize(
        ("language", "path", "content"),
        (
            ("typescript", "src/example.ts", "class ExampleValue { example_value = 1; }\n"),
            ("php", "src/example.php", "<?php\nclass ExampleValue { public int $example_value = 1; }\n"),
        ),
    )
    def test_manifest_marks_unavailable_assigned_value_evidence_as_unsupported(
        self, language: str, path: str, content: str
    ) -> None:
        root = self.project({path: content})
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map(language, root, self.scan_policy()), format
            )
        )

        assert tuple(
            (value.kind, value.expression, value.reference)
            for attribute in manifest.attributes
            for value in attribute.assigned_values
        ) == ((SourceAssignedValueKind.UNSUPPORTED, "", ""),)

    @pytest.mark.parametrize(
        ("language", "path", "content", "expected"),
        (
            ("python", "src/example.py", "class ExampleValue:\n    example_value: int\n", CapabilityStatus.SUPPORTED),
            (
                "typescript",
                "src/example.ts",
                "class ExampleValue { example_value: number; }\n",
                CapabilityStatus.UNSUPPORTED,
            ),
            (
                "php",
                "src/example.php",
                "<?php\nclass ExampleValue { public int $example_value; }\n",
                CapabilityStatus.UNSUPPORTED,
            ),
        ),
    )
    def test_extractors_report_assigned_value_capability_honestly(
        self, language: str, path: str, content: str, expected: CapabilityStatus
    ) -> None:
        code_map = self.application.generate_map(language, self.project({path: content}), self.scan_policy())

        coverage = next(
            item for item in code_map.producer.capabilities if item.capability is FactCapability.ASSIGNED_VALUES
        )
        assert coverage.status is expected
