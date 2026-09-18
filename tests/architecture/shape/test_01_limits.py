import pytest

from .base_test import ShapeTestCase


class TestShapeLimits(ShapeTestCase):
    @pytest.mark.parametrize(
        ("rule", "source", "actual"),
        (
            ("max_classes_per_file", "class ExampleFirst: pass\nclass ExampleSecond: pass\n", 2),
            ("max_functions_per_file", "def example_first(): pass\ndef example_second(): pass\n", 2),
            (
                "max_methods_per_class",
                "class ExampleValue:\n    def example_first(self): pass\n    def example_second(self): pass\n",
                2,
            ),
            ("max_declared_args", "def example_function(example_a, example_b): pass\n", 2),
            ("max_function_lines", "def example_function():\n    example_value = 1\n    return example_value\n", 3),
            (
                "max_method_lines",
                "class ExampleValue:\n    def example_method(self):\n        example_value = 1\n"
                "        return example_value\n",
                3,
            ),
            ("max_class_lines", "class ExampleValue:\n    example_first: int\n    example_second: str\n", 3),
        ),
    )
    @pytest.mark.parametrize("offset", (-1, 0, 1))
    def test_limits_report_only_values_above_the_threshold(
        self, rule: str, source: str, actual: int, offset: int
    ) -> None:
        code_map = self.application.generate_queryable_map(
            "python", self.project({"example.py": source}), self.scan_policy()
        )
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
            assert violations[0].source_id == "example.py"
        else:
            assert violations == ()

    @pytest.mark.parametrize(
        ("rule", "source"),
        (
            ("allow_optional_function_args", "def example_function(example_value: str = ''): pass\n"),
            (
                "allow_optional_method_args",
                "class ExampleValue:\n    def example_method(self, example_value: str = ''): pass\n",
            ),
            ("allow_optional_class_properties", "class ExampleValue:\n    example_value: str | None\n"),
            ("allow_import_aliases", "import json as example_json\n"),
        ),
    )
    @pytest.mark.parametrize("allowed", (False, True))
    def test_boolean_permissions_apply_to_the_public_report(self, rule: str, source: str, allowed: bool) -> None:
        code_map = self.application.generate_queryable_map(
            "python", self.project({"example.py": source}), self.scan_policy()
        )
        config = self.application.configure(
            {"shape": {"realms": [{"name": "example-source", "match": "*", "shape": {rule: allowed}}]}}
        )
        violations = self.report("architecture.violations.shape", config, code_map).violations
        assert any(item.rule_name == rule for item in violations) is not allowed
