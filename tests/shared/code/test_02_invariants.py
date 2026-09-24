import json

from ...support.code_map import CodeMapFactory
from ...support.service_test import ServiceTestCase


class TestPublicCodeValues(ServiceTestCase):
    def test_query_filters_are_composable_without_changing_the_original_query(self) -> None:
        result = CodeMapFactory().queryable(
            {
                "example.source": {
                    "classes": [
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
        assert original.schema_version == 3
        assert set(json.loads(original.to_json())) == {"language", "extraction", "dependency_graph"}

    def test_query_surfaces_keep_external_and_tracked_edges_distinct(self) -> None:
        result = CodeMapFactory().queryable(
            {
                "example_values.source": {
                    "classes": [CodeMapFactory().source_class("ExampleValue", line_count=1, methods=(), properties=())]
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
