from modwire.architecture import ArchitectureConfig, ShapeReport
from tests.architecture.shape.base_test import ShapeTestCase


class TestShapeInvariants(ShapeTestCase):
    def test_each_matching_realm_keeps_its_rules(self) -> None:
        config = ArchitectureConfig.model_validate({"shape": {"realms": [
            {"name": "example-source", "match": "src/*"},
            {"name": "example-repository", "match": "*"},
        ]}})
        report = self.report(ShapeReport, config, self.queryable_map(("src/example.py",), ()))
        assert tuple((item.realm, item.rule_name) for item in report.violations) == (
            ("example-source", "max_functions_per_file"), ("example-repository", "max_functions_per_file"),
        )

    def test_scoped_exception_does_not_relax_other_sources(self) -> None:
        config = ArchitectureConfig.model_validate({"shape": {"realms": [
            {"name": "example-source", "match": "src", "excluded_patterns": ["src/example_entry.py"]},
            {"name": "example-entry", "match": "src/example_entry.py", "shape": {"max_functions_per_file": 1}},
        ]}})
        report = self.report(ShapeReport, config, self.queryable_map(("src/example_entry.py", "src/example_service.py"), ()))
        assert tuple((item.source_id, item.rule_name) for item in report.violations) == (
            ("src/example_service.py", "max_functions_per_file"),
        )
