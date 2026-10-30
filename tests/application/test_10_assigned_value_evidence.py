from modwire.application import SourceAssignedValueKind

from .base_test import ApplicationTestCase


class TestAssignedValueEvidence(ApplicationTestCase):
    def test_python_manifest_publishes_ordered_assigned_value_evidence(self) -> None:
        root = self.repository / "tests/fixtures/code_map/language_extensions/python"
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map("python", root, self.scan_policy()), format
            )
        )
        owner_id = next(item.id for item in manifest.symbols if item.id.qualified_name == "ExampleAssignedValues")
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
