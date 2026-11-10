import pytest

from ...support.code_map import CodeMapFactory
from .base_test import ShapeTestCase


class TestShapeLimits(ShapeTestCase):
    @pytest.mark.parametrize(
        ("language", "path"),
        (
            ("ruby", "src/example.rb"),
            ("php", "src/example.php"),
        ),
    )
    def test_module_and_trait_methods_obey_method_limits(self, language: str, path: str) -> None:
        root = self.repository / "tests/fixtures/shape" / language
        code_map = self.application.generate_queryable_map(language, str(root), self.scan_policy())
        config = self.application.configure(
            {
                "shape": {
                    "realms": [
                        {
                            "name": "example-source",
                            "match": "src",
                            "shape": {"max_method_lines": 1, "max_declared_args": 1},
                        }
                    ]
                }
            }
        )

        violations = self.report("architecture.violations.shape", config, code_map).violations

        assert {(item.source_id, item.symbol_kind, item.symbol_name, item.rule_name) for item in violations} == {
            (path, "method", "example_method", "max_method_lines"),
            (path, "method", "example_method", "max_declared_args"),
            (path, "method", "example_method", "allow_optional_method_args"),
        }

        allowed = self.application.configure(
            {
                "shape": {
                    "realms": [
                        {
                            "name": "example-source",
                            "match": "src",
                            "shape": {
                                "max_method_lines": 3,
                                "max_declared_args": 2,
                                "allow_optional_method_args": True,
                            },
                        }
                    ]
                }
            }
        )
        assert self.report("architecture.violations.shape", allowed, code_map).violations == ()

    @pytest.mark.parametrize(
        ("rule", "source_file", "actual"),
        (
            (
                "max_classes_per_file",
                {
                    "declarations": [
                        CodeMapFactory().source_class("ExampleFirst", line_count=1, methods=(), properties=()),
                        CodeMapFactory().source_class("ExampleSecond", line_count=1, methods=(), properties=()),
                    ]
                },
                2,
            ),
            (
                "max_functions_per_file",
                {
                    "functions": [
                        CodeMapFactory().source_function(
                            "example_first", line_count=1, parameter_count=0, optional_parameter_count=0
                        ),
                        CodeMapFactory().source_function(
                            "example_second", line_count=1, parameter_count=0, optional_parameter_count=0
                        ),
                    ]
                },
                2,
            ),
            (
                "max_variables_per_file",
                {
                    "values": [
                        CodeMapFactory().source_value("example_first", declaration_kind="assignment", scope="module"),
                        CodeMapFactory().source_value("example_second", declaration_kind="assignment", scope="module"),
                    ]
                },
                2,
            ),
            (
                "max_methods_per_class",
                {
                    "declarations": [
                        CodeMapFactory().source_class(
                            "ExampleValue",
                            line_count=1,
                            methods=(
                                CodeMapFactory().source_method(
                                    "example_first", line_count=1, parameter_count=0, optional_parameter_count=0
                                ),
                                CodeMapFactory().source_method(
                                    "example_second", line_count=1, parameter_count=0, optional_parameter_count=0
                                ),
                            ),
                            properties=(),
                        )
                    ]
                },
                2,
            ),
            (
                "max_declared_args",
                {
                    "functions": [
                        CodeMapFactory().source_function(
                            "example_function", line_count=1, parameter_count=2, optional_parameter_count=0
                        )
                    ]
                },
                2,
            ),
            (
                "max_function_lines",
                {
                    "functions": [
                        CodeMapFactory().source_function(
                            "example_function", line_count=3, parameter_count=0, optional_parameter_count=0
                        )
                    ]
                },
                3,
            ),
            (
                "max_method_lines",
                {
                    "declarations": [
                        CodeMapFactory().source_class(
                            "ExampleValue",
                            line_count=1,
                            methods=(
                                CodeMapFactory().source_method(
                                    "example_method", line_count=3, parameter_count=0, optional_parameter_count=0
                                ),
                            ),
                            properties=(),
                        )
                    ]
                },
                3,
            ),
            (
                "max_class_lines",
                {
                    "declarations": [
                        CodeMapFactory().source_class("ExampleValue", line_count=3, methods=(), properties=())
                    ]
                },
                3,
            ),
        ),
    )
    @pytest.mark.parametrize("offset", (-1, 0, 1))
    def test_limits_report_only_values_above_the_threshold(
        self, rule: str, source_file: dict[str, object], actual: int, offset: int
    ) -> None:
        code_map = CodeMapFactory().queryable({"example.source": source_file}, ())
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

    def test_variable_limit_defaults_to_zero_and_counts_only_module_assignments(self) -> None:
        code_map = CodeMapFactory().queryable(
            {
                "example.source": {
                    "values": [
                        CodeMapFactory().source_value("example_module", declaration_kind="assignment", scope="module"),
                        CodeMapFactory().source_value("EXAMPLE_CONSTANT", declaration_kind="constant", scope="module"),
                        CodeMapFactory().source_value("example_local", declaration_kind="assignment", scope="local"),
                        CodeMapFactory().source_value("example_member", declaration_kind="assignment", scope="member"),
                    ]
                }
            },
            (),
        )
        config = self.application.configure({"shape": {"realms": [{"name": "example-source", "match": "*"}]}})
        violations = tuple(
            item
            for item in self.report("architecture.violations.shape", config, code_map).violations
            if item.rule_name == "max_variables_per_file"
        )
        assert len(violations) == 1
        assert violations[0].actual == 1
        assert violations[0].limit == 0

    def test_negative_one_disables_the_variable_limit(self) -> None:
        code_map = CodeMapFactory().queryable(
            {
                "example.source": {
                    "values": [
                        CodeMapFactory().source_value("example_module", declaration_kind="assignment", scope="module")
                    ]
                }
            },
            (),
        )
        config = self.application.configure(
            {
                "shape": {
                    "realms": [
                        {
                            "name": "example-source",
                            "match": "*",
                            "shape": {"max_variables_per_file": -1},
                        }
                    ]
                }
            }
        )
        assert all(
            item.rule_name != "max_variables_per_file"
            for item in self.report("architecture.violations.shape", config, code_map).violations
        )

    @pytest.mark.parametrize(
        ("rule", "source_file"),
        (
            (
                "allow_optional_function_args",
                {
                    "functions": [
                        CodeMapFactory().source_function(
                            "example_function", line_count=1, parameter_count=1, optional_parameter_count=1
                        )
                    ]
                },
            ),
            (
                "allow_optional_method_args",
                {
                    "declarations": [
                        CodeMapFactory().source_class(
                            "ExampleValue",
                            line_count=1,
                            methods=(
                                CodeMapFactory().source_method(
                                    "example_method", line_count=1, parameter_count=1, optional_parameter_count=1
                                ),
                            ),
                            properties=(),
                        )
                    ]
                },
            ),
            (
                "allow_optional_class_properties",
                {
                    "declarations": [
                        CodeMapFactory().source_class(
                            "ExampleValue",
                            line_count=1,
                            methods=(),
                            properties=({"name": "example_value", "is_optional": True},),
                        )
                    ]
                },
            ),
            (
                "allow_import_aliases",
                {
                    "imports": [
                        CodeMapFactory().source_import(
                            "example_external", imported_name="", is_aliased=True, imported_symbols=()
                        )
                    ]
                },
            ),
        ),
    )
    @pytest.mark.parametrize("allowed", (False, True))
    def test_boolean_permissions_apply_to_the_public_report(
        self, rule: str, source_file: dict[str, object], allowed: bool
    ) -> None:
        code_map = CodeMapFactory().queryable({"example.source": source_file}, ())
        config = self.application.configure(
            {"shape": {"realms": [{"name": "example-source", "match": "*", "shape": {rule: allowed}}]}}
        )
        violations = self.report("architecture.violations.shape", config, code_map).violations
        assert any(item.rule_name == rule for item in violations) is not allowed
