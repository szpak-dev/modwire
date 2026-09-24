import pytest

from ..base_test import ExtractionTestCase


class TestNativeSymbols(ExtractionTestCase):
    @pytest.mark.parametrize("language", ("python", "typescript", "php"))
    def test_native_extractors_preserve_abstract_and_concrete_class_members(self, language: str) -> None:
        root = self.repository / "tests/fixtures/syntax" / language
        result = self.application.generate_queryable_map(language, root, self.scan_policy())
        abstract = result.abstract_classes().first().item
        assert tuple(item.name for item in abstract.abstract_methods) == ("example_required",)
        assert tuple(item.name for item in abstract.concrete_methods) == ("example_concrete",)
        concrete = result.classes().where_equal(lambda item: item.item.name, "ExampleImplementation").first().item
        assert tuple(item.name for item in concrete.methods) == ("example_required",)
        assert concrete.properties[0].name == "example_optional"
        assert concrete.properties[0].is_optional

    @pytest.mark.parametrize("language", ("typescript", "php"))
    def test_interfaces_expose_method_signatures(self, language: str) -> None:
        root = self.repository / "tests/fixtures/syntax" / language
        result = self.application.generate_queryable_map(language, root, self.scan_policy())
        interface = result.interfaces().first().item
        assert interface.name == "ExampleContract"
        assert interface.methods[0].name == "example_required"
        assert interface.methods[0].declared_args == 1

    def test_typescript_callable_object_keeps_optional_signature_arguments(self) -> None:
        root = self.repository / "tests/fixtures/syntax/typescript"
        result = self.application.generate_queryable_map("typescript", root, self.scan_policy())
        callback = result.types().where_equal(lambda item: item.item.name, "ExampleCallableObject").first().item
        assert callback.signatures[0].declared_args == 2
        assert callback.signatures[0].optional_args == 1

    def test_python_async_arguments_and_top_level_callable_scope_are_preserved(self) -> None:
        root = self.repository / "tests/fixtures/syntax/python"
        result = self.application.generate_queryable_map("python", root, self.scan_policy())
        asynchronous = result.functions().where_equal(lambda item: item.item.name, "example_async").first().item
        assert asynchronous.declared_args == 2
        assert asynchronous.optional_args == 1
        names = {item.item.qualified_name for item in result.callables().all()}
        assert {"example_async", "example_outer"} <= names
        assert all(item.item.name != "example_inner" for item in result.callables().all())

    def test_typescript_function_alias_retains_the_baseline_type_without_signature_details(self) -> None:
        root = self.repository / "tests/fixtures/syntax/typescript"
        result = self.application.generate_queryable_map("typescript", root, self.scan_policy())
        callback = result.types().where_equal(lambda item: item.item.name, "ExampleCallback").first().item
        assert callback.visibility == "public"
        assert callback.signatures == []

    @pytest.mark.parametrize("language", ("python", "typescript", "php"))
    def test_module_variable_shape_is_language_neutral(self, language: str) -> None:
        root = self.repository / "tests/fixtures/syntax" / language
        result = self.application.generate_queryable_map(language, root, self.scan_policy())
        variable = result.values().where_equal(lambda item: item.item.name, "example_variable").first().item
        constant = result.values().where_equal(lambda item: item.item.name, "EXAMPLE_CONSTANT").first().item
        assert variable.scope == constant.scope == "module"
        assert variable.declaration_kind == "assignment"
        assert constant.declaration_kind == "constant"

        config = self.application.configure({"shape": {"realms": [{"name": "syntax", "match": "*"}]}})
        shape = next(
            item
            for item in self.application.analyze(result, config)
            if item.metadata.id == "architecture.violations.shape"
        )
        violations = tuple(item for item in shape.violations if item.rule_name == "max_variables_per_file")
        assert len(violations) == 1
        assert violations[0].actual == 1
        assert violations[0].limit == 0
