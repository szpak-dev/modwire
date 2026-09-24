from ...support.code_map import CodeMapFactory
from .base_test import ShapeTestCase


class TestShapeInvariants(ShapeTestCase):
    def test_file_limits_count_each_source_independently(self) -> None:
        factory = CodeMapFactory()
        code_map = factory.queryable(
            {
                "src/example_first.source": {
                    "functions": [
                        factory.symbol("example_first", line_count=1, declared_args=0, optional_args=0),
                        factory.symbol("example_second", line_count=1, declared_args=0, optional_args=0),
                    ]
                },
                "src/example_other.source": {
                    "functions": [factory.symbol("example_other", line_count=1, declared_args=0, optional_args=0)]
                },
            },
            (),
        )
        config = self.application.configure(
            {
                "shape": {
                    "realms": [
                        {
                            "name": "example-source",
                            "match": "src",
                            "shape": {"max_functions_per_file": 1},
                        }
                    ]
                }
            }
        )

        report = self.report("architecture.violations.shape", config, code_map)

        violations = tuple(item for item in report.violations if item.rule_name == "max_functions_per_file")
        assert tuple((item.source_id, item.actual, item.limit) for item in violations) == (
            ("src/example_first.source", 2, 1),
        )

    def test_each_matching_realm_keeps_its_rules(self) -> None:
        config = self.application.configure(
            {
                "shape": {
                    "realms": [
                        {"name": "example-source", "match": "src/*"},
                        {"name": "example-repository", "match": "*"},
                    ]
                }
            }
        )
        report = self.report("architecture.violations.shape", config, self.queryable_map(("src/example.source",), ()))
        assert tuple((item.realm, item.rule_name) for item in report.violations) == (
            ("example-source", "max_functions_per_file"),
            ("example-repository", "max_functions_per_file"),
        )

    def test_scoped_exception_does_not_relax_other_sources(self) -> None:
        config = self.application.configure(
            {
                "shape": {
                    "realms": [
                        {
                            "name": "example-source",
                            "match": "src",
                            "excluded_patterns": ["src/example_entry.source"],
                        },
                        {
                            "name": "example-entry",
                            "match": "src/example_entry.source",
                            "shape": {"max_functions_per_file": 1},
                        },
                    ]
                }
            }
        )
        report = self.report(
            "architecture.violations.shape",
            config,
            self.queryable_map(("src/example_entry.source", "src/example_service.source"), ()),
        )
        assert tuple((item.source_id, item.rule_name) for item in report.violations) == (
            ("src/example_service.source", "max_functions_per_file"),
        )
