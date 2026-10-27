import pytest

from modwire.application import SourceAssignedValueKind

from ..support.code_map_fixture.language_capability_matrix.limits.capability.value import (
    AssignedValueLimitationExpectation,
)
from ..support.code_map_fixture.language_capability_matrix.reader import LanguageCapabilityMatrixReader
from .base_test import ApplicationTestCase


class TestAssignedValueEvidence(ApplicationTestCase):
    capability_matrix = LanguageCapabilityMatrixReader().read(
        ApplicationTestCase.repository / "language-capabilities.yaml"
    )
    assigned_value_limitation_cases = tuple(
        (language, limitation)
        for language, row in capability_matrix.languages.items()
        for limitation in row.capability_limitations.assigned_values
    )

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

    @pytest.mark.parametrize(
        ("language", "limitation"),
        assigned_value_limitation_cases,
        ids=[f"{language}-{limitation.scenario}" for language, limitation in assigned_value_limitation_cases],
    )
    def test_manifest_matches_the_matrix_assigned_value_limitation(
        self,
        language: str,
        limitation: AssignedValueLimitationExpectation,
    ) -> None:
        row = self.capability_matrix.languages[language]
        root = self.repository / row.fixtures.capability_gap_root
        scenario = next(scenario for scenario in row.scenarios if scenario.scenario == limitation.scenario)
        assert (root / scenario.source).is_file()
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map(language, root, self.scan_policy()), format
            )
        )

        observed = {
            attribute.name: tuple(value.kind for value in attribute.assigned_values)
            for attribute in manifest.attributes
        }

        assert set(limitation.present_attribute_names) <= set(observed)
        assert set(limitation.absent_attribute_names).isdisjoint(observed)
        assert all(observed[name] == kinds for name, kinds in limitation.expected_value_kinds.items())
