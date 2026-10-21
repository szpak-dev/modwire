import json

import pytest

from modwire.application import CodeMap, CodeValidationError, CodeViolation

from ...support.code_map import CodeMapFactory
from ...support.service_test import ServiceTestCase


class TestPublicCodeValues(ServiceTestCase):
    def code_map_with_call(self) -> CodeMap:
        source_id = "example.source"
        return (
            CodeMapFactory()
            .queryable(
                {
                    source_id: {
                        "callables": [
                            CodeMapFactory().source_callable(source_id, "example_target"),
                            CodeMapFactory().source_callable(source_id, "example_caller"),
                        ],
                        "calls": [CodeMapFactory().source_call(source_id, "example_caller", "example_target")],
                    }
                },
                (),
            )
            .code_map
        )

    def test_query_filters_are_composable_without_changing_the_original_query(self) -> None:
        result = CodeMapFactory().queryable(
            {
                "example.source": {
                    "declarations": [
                        CodeMapFactory().source_class("ExampleFirst", line_count=1, methods=(), properties=()),
                        CodeMapFactory().source_class("ExampleSecond", line_count=1, methods=(), properties=()),
                        CodeMapFactory().source_class("ExampleThird", line_count=1, methods=(), properties=()),
                    ]
                }
            },
            (),
        )
        original = result.classes()
        selected = original.where_contains(lambda item: item.item.name, "example", case_sensitive=False)
        selected = selected.where_equal(lambda item: item.item.name, "ExampleSecond")
        assert selected.count() == 1
        assert selected.first().item.name == "ExampleSecond"
        assert original.count() == 3
        assert original.where_contains(lambda item: item.item.name, "example", case_sensitive=True).all() == ()
        assert original.where_equal(lambda item: item.item.name, "ExampleMissing").first() is None

    def test_incoming_and_outgoing_queries_preserve_edge_direction(self) -> None:
        paths = ("example_first.source", "example_second.source", "example_third.source")
        result = CodeMapFactory().queryable(
            dict.fromkeys(paths, {}),
            (
                (paths[0], paths[1], "resolved", "example_second"),
                (paths[1], paths[2], "resolved", "example_third"),
            ),
        )
        assert result.outgoing_dependencies(paths[0]).first().edge.to_id == paths[1]
        assert result.incoming_dependencies(paths[2]).first().edge.from_id == paths[1]
        assert result.incoming_dependencies(paths[0]).all() == ()
        assert result.outgoing_dependencies(paths[2]).all() == ()
        assert result.dependencies_between(paths[2], paths[1]).all() == ()

    def test_code_map_round_trips_json(self) -> None:
        original = CodeMapFactory().queryable({"src/example.source": {}}, ()).code_map
        restored = type(original).model_validate_json(original.to_json())
        assert restored.to_dict() == original.to_dict()
        assert original.schema_version == 11
        assert set(json.loads(original.to_json())) == {
            "language",
            "producer",
            "extraction",
            "dependency_graph",
        }

    def test_source_file_rejects_duplicate_call_facts(self) -> None:
        original = self.code_map_with_call()
        source_file = original.extraction.files["example.source"]
        tampered_file = source_file.model_copy(update={"calls": [*source_file.calls, source_file.calls[0]]})
        tampered = original.model_copy(
            update={"extraction": original.extraction.model_copy(update={"files": {"example.source": tampered_file}})}
        )

        with pytest.raises(CodeValidationError) as raised:
            CodeMap.model_validate_json(tampered.model_dump_json())

        assert raised.value.violation is CodeViolation.DUPLICATE_CALL

    def test_source_file_rejects_an_unknown_call_source_callable(self) -> None:
        original = self.code_map_with_call()
        source_file = original.extraction.files["example.source"]
        call = source_file.calls[0]
        unknown = call.source_callable_id.model_copy(update={"qualified_name": "example_missing"})
        tampered_file = source_file.model_copy(
            update={"calls": [call.model_copy(update={"source_callable_id": unknown})]}
        )
        tampered = original.model_copy(
            update={"extraction": original.extraction.model_copy(update={"files": {"example.source": tampered_file}})}
        )

        with pytest.raises(CodeValidationError) as raised:
            CodeMap.model_validate_json(tampered.model_dump_json())

        assert raised.value.violation is CodeViolation.UNKNOWN_CALL_SOURCE_CALLABLE

    def test_source_file_rejects_foreign_call_ownership(self) -> None:
        original = self.code_map_with_call()
        source_file = original.extraction.files["example.source"]
        call = source_file.calls[0]
        tampered_file = source_file.model_copy(
            update={"calls": [call.model_copy(update={"source_id": "example_foreign.source"})]}
        )
        tampered = original.model_copy(
            update={"extraction": original.extraction.model_copy(update={"files": {"example.source": tampered_file}})}
        )

        with pytest.raises(CodeValidationError) as raised:
            CodeMap.model_validate_json(tampered.model_dump_json())

        assert raised.value.violation is CodeViolation.FOREIGN_CALL_SOURCE

    def test_code_map_rejects_an_unknown_resolved_call_target(self) -> None:
        original = self.code_map_with_call()
        source_file = original.extraction.files["example.source"]
        call = source_file.calls[0]
        assert call.target_callable_id is not None
        unknown = call.target_callable_id.model_copy(update={"qualified_name": "example_missing"})
        tampered_file = source_file.model_copy(
            update={"calls": [call.model_copy(update={"target_callable_id": unknown})]}
        )
        tampered = original.model_copy(
            update={"extraction": original.extraction.model_copy(update={"files": {"example.source": tampered_file}})}
        )

        with pytest.raises(CodeValidationError) as raised:
            CodeMap.model_validate_json(tampered.model_dump_json())

        assert raised.value.violation is CodeViolation.UNKNOWN_RESOLVED_CALL_TARGET

    def test_query_surfaces_keep_external_and_tracked_edges_distinct(self) -> None:
        result = CodeMapFactory().queryable(
            {
                "example_values.source": {
                    "declarations": [
                        CodeMapFactory().source_class("ExampleValue", line_count=1, methods=(), properties=())
                    ]
                },
                "example_consumer.source": {},
            },
            (
                ("example_consumer.source", "example_values.source", "resolved", "example_values"),
                ("example_consumer.source", None, "external", "example_external"),
            ),
        )
        assert result.files().count() == result.source_files().count() == 2
        assert result.classes().where_equal(lambda item: item.item.name, "ExampleValue").count() == 1
        assert result.tracked_dependency_edges().count() == 1
        assert result.external_dependency_edges().count() == 1
        assert result.dependencies_between("example_consumer.source", "example_values.source").count() == 1
        assert result.source_file("example_missing.source") is None
