from ..base_test import ExtractionTestCase


class TestDependencyInvariants(ExtractionTestCase):
    def test_ambiguous_module_suffix_does_not_choose_an_arbitrary_target(self) -> None:
        result = self.extract(
            {
                "example_first/example_package/example_value.py": "class ExampleValue:\n    pass\n",
                "example_second/example_package/example_value.py": "class ExampleValue:\n    pass\n",
                "example_consumer.py": "from example_first.example_package.example_value import ExampleValue\n",
            }
        )
        edge = result.dependency_edges().first().edge
        assert edge.resolution == "unresolved"
        assert edge.to_id is None
        assert not result.tracked_dependency_edges().all()

    def test_resolves_imports_between_supplied_sources(self) -> None:
        result = self.extract(
            {
                "example_package/example_value.py": "class ExampleValue:\n    pass\n",
                "example_package/example_consumer.py": "from example_package.example_value import ExampleValue\n",
            }
        )
        edges = result.tracked_dependency_edges().all()
        assert len(edges) == 1
        assert edges[0].edge.to_id == "example_package/example_value.py"
        assert edges[0].edge.resolution == "resolved"

    def test_external_import_has_no_tracked_target(self) -> None:
        result = self.extract({"example.py": "import json\n"})
        edge = result.external_dependency_edges().first().edge
        assert edge.specifier == "json"
        assert edge.resolution == "external"
        assert edge.to_id is None

    def test_unresolved_relative_import_remains_queryable(self) -> None:
        result = self.extract({"example_package/example.py": "from .example_missing import ExampleValue\n"})
        edge = result.dependency_edges().first().edge
        assert edge.resolution == "unresolved"
        assert edge.to_id is None
