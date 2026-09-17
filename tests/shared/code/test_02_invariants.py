import json

from ...extraction.base_test import ExtractionTestCase


class TestPublicCodeValues(ExtractionTestCase):
    def test_query_filters_are_composable_without_changing_the_original_query(self) -> None:
        result = self.extract(
            {"example.py": "class ExampleFirst: pass\nclass ExampleSecond: pass\nclass ExampleThird: pass\n"}
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
        result = self.extract(
            {
                "example_first.py": "import example_second\n",
                "example_second.py": "import example_third\n",
                "example_third.py": "",
            }
        )
        assert result.outgoing_dependencies("example_first.py").first().edge.to_id == "example_second.py"
        assert result.incoming_dependencies("example_third.py").first().edge.from_id == "example_second.py"
        assert result.incoming_dependencies("example_first.py").all() == ()
        assert result.outgoing_dependencies("example_third.py").all() == ()
        assert result.dependencies_between("example_third.py", "example_second.py").all() == ()

    def test_code_map_round_trips_json(self) -> None:
        original = self.extract({"src/example.py": "import json\n"}).code_map
        restored = type(original).model_validate_json(original.to_json())
        assert restored.to_dict() == original.to_dict()
        assert set(json.loads(original.to_json())) == {"language", "extraction", "dependency_graph"}

    def test_query_surfaces_keep_external_and_tracked_edges_distinct(self) -> None:
        result = self.extract(
            {
                "example_values.py": "class ExampleValue:\n    pass\n",
                "example_consumer.py": "import json\nfrom example_values import ExampleValue\n",
            }
        )
        assert result.files().count() == result.source_files().count() == 2
        assert result.classes().where_equal(lambda item: item.item.name, "ExampleValue").count() == 1
        assert result.tracked_dependency_edges().count() == 1
        assert result.external_dependency_edges().count() == 1
        assert result.dependencies_between("example_consumer.py", "example_values.py").count() == 1
        assert result.source_file("example_missing.py") is None
