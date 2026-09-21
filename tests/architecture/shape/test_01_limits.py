import pytest

from ...support.code_map import CodeMapFactory
from .base_test import ShapeTestCase


class TestShapeLimits(ShapeTestCase):
    @pytest.mark.parametrize(
        ("rule", "source_file", "actual"),
        (
            (
                "max_classes_per_file",
                {
                    "classes": [
                        CodeMapFactory.source_class("ExampleFirst"),
                        CodeMapFactory.source_class("ExampleSecond"),
                    ]
                },
                2,
            ),
            (
                "max_functions_per_file",
                {"functions": [CodeMapFactory.symbol("example_first"), CodeMapFactory.symbol("example_second")]},
                2,
            ),
            (
                "max_methods_per_class",
                {
                    "classes": [
                        CodeMapFactory.source_class(
                            "ExampleValue",
                            methods=(CodeMapFactory.symbol("example_first"), CodeMapFactory.symbol("example_second")),
                        )
                    ]
                },
                2,
            ),
            (
                "max_declared_args",
                {"functions": [CodeMapFactory.symbol("example_function", declared_args=2)]},
                2,
            ),
            (
                "max_function_lines",
                {"functions": [CodeMapFactory.symbol("example_function", line_count=3)]},
                3,
            ),
            (
                "max_method_lines",
                {
                    "classes": [
                        CodeMapFactory.source_class(
                            "ExampleValue", methods=(CodeMapFactory.symbol("example_method", line_count=3),)
                        )
                    ]
                },
                3,
            ),
            ("max_class_lines", {"classes": [CodeMapFactory.source_class("ExampleValue", line_count=3)]}, 3),
        ),
    )
    @pytest.mark.parametrize("offset", (-1, 0, 1))
    def test_limits_report_only_values_above_the_threshold(
        self, rule: str, source_file: dict[str, object], actual: int, offset: int
    ) -> None:
        code_map = CodeMapFactory.queryable({"example.source": source_file})
        config = self.application.configure(
            {"shape": {"realms": [{"name": "example-source", "match": "*", "shape": {rule: actual + offset}}]}}
        )
        violations = tuple(
            item
            for item in self.report("architecture.violations.shape", config, code_map).violations
            if item.rule_name == rule
        )
        if offset < 0:
            assert len(violations) == 1
            assert violations[0].actual == actual
            assert violations[0].limit == actual + offset
            assert violations[0].source_id == "example.source"
        else:
            assert violations == ()

    @pytest.mark.parametrize(
        ("rule", "source_file"),
        (
            (
                "allow_optional_function_args",
                {"functions": [CodeMapFactory.symbol("example_function", declared_args=1, optional_args=1)]},
            ),
            (
                "allow_optional_method_args",
                {
                    "classes": [
                        CodeMapFactory.source_class(
                            "ExampleValue",
                            methods=(CodeMapFactory.symbol("example_method", declared_args=1, optional_args=1),),
                        )
                    ]
                },
            ),
            (
                "allow_optional_class_properties",
                {
                    "classes": [
                        CodeMapFactory.source_class(
                            "ExampleValue", properties=({"name": "example_value", "is_optional": True},)
                        )
                    ]
                },
            ),
            (
                "allow_import_aliases",
                {"imports": [CodeMapFactory.source_import("example_external", is_aliased=True)]},
            ),
        ),
    )
    @pytest.mark.parametrize("allowed", (False, True))
    def test_boolean_permissions_apply_to_the_public_report(
        self, rule: str, source_file: dict[str, object], allowed: bool
    ) -> None:
        code_map = CodeMapFactory.queryable({"example.source": source_file})
        config = self.application.configure(
            {"shape": {"realms": [{"name": "example-source", "match": "*", "shape": {rule: allowed}}]}}
        )
        violations = self.report("architecture.violations.shape", config, code_map).violations
        assert any(item.rule_name == rule for item in violations) is not allowed
