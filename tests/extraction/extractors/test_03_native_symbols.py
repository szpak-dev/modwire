import pytest

from ...support.code_map_fixture import FixtureLanguageConvention
from ..base_test import ExtractionTestCase

CALL_OCCURRENCE_FIXTURES = ExtractionTestCase.repository / "tests/fixtures/call_occurrences"
LANGUAGE_EXTENSIONS = ExtractionTestCase.repository / "tests/fixtures/code_map/language_extensions"


class TestNativeSymbols(ExtractionTestCase):
    def test_authored_identical_calls_keep_distinct_occurrence_identities(self) -> None:
        languages = self.application.discover(CALL_OCCURRENCE_FIXTURES, self.scan_policy())

        for language in languages:
            root = CALL_OCCURRENCE_FIXTURES / language
            first = self.application.generate_queryable_map(language, root, self.scan_policy())
            second = self.application.generate_queryable_map(language, root, self.scan_policy())

            calls = tuple(item.item for item in first.calls().all())
            assert tuple(item.ordinal for item in calls) == (1, 2)
            assert len({item.identity() for item in calls}) == 2
            assert len({item.source_callable_id.canonical() for item in calls}) == 1
            assert len({item.expression for item in calls}) == 1
            assert first.code_map.to_dict() == second.code_map.to_dict()

    @pytest.mark.parametrize(
        "convention",
        (
            FixtureLanguageConvention.PYTHON,
            FixtureLanguageConvention.TYPESCRIPT,
            FixtureLanguageConvention.PHP,
            FixtureLanguageConvention.JAVA,
        ),
        ids=lambda convention: convention.language,
    )
    def test_native_extractors_preserve_abstract_and_concrete_class_methods(
        self, convention: FixtureLanguageConvention
    ) -> None:
        root = LANGUAGE_EXTENSIONS / convention.language
        result = self.application.generate_queryable_map(convention.language, root, self.scan_policy())
        abstract = result.abstract_classes().first().item
        assert tuple(item.name for item in abstract.abstract_methods) == (convention.member_name("example_required"),)
        assert tuple(item.name for item in abstract.methods) == (convention.member_name("example_concrete"),)
        concrete = result.classes().where_equal(lambda item: item.item.name, "ExampleImplementation").first().item
        assert convention.member_name("example_required") in tuple(item.name for item in concrete.methods)

    @pytest.mark.parametrize(
        "convention",
        (
            FixtureLanguageConvention.PYTHON,
            FixtureLanguageConvention.TYPESCRIPT,
            FixtureLanguageConvention.PHP,
        ),
        ids=lambda convention: convention.language,
    )
    def test_nullable_class_members_remain_optional(self, convention: FixtureLanguageConvention) -> None:
        root = LANGUAGE_EXTENSIONS / convention.language
        result = self.application.generate_queryable_map(convention.language, root, self.scan_policy())
        concrete = result.classes().where_equal(lambda item: item.item.name, "ExampleImplementation").first().item
        assert concrete.properties[0].name == convention.member_name("example_optional")
        assert concrete.properties[0].is_optional

    @pytest.mark.parametrize(
        "convention",
        (
            FixtureLanguageConvention.TYPESCRIPT,
            FixtureLanguageConvention.PHP,
            FixtureLanguageConvention.JAVA,
        ),
        ids=lambda convention: convention.language,
    )
    def test_interfaces_expose_method_signatures(self, convention: FixtureLanguageConvention) -> None:
        root = LANGUAGE_EXTENSIONS / convention.language
        result = self.application.generate_queryable_map(convention.language, root, self.scan_policy())
        interface = result.interfaces().first().item
        assert interface.name == "ExampleContract"
        assert interface.methods[0].name == convention.member_name("example_required")
        assert interface.methods[0].declared_args == 1

    def test_java_declaration_forms_use_shared_symbol_families(self) -> None:
        root = LANGUAGE_EXTENSIONS / "java"
        result = self.application.generate_queryable_map("java", root, self.scan_policy())
        declarations = {item.item.name: item.item.kind for item in result.declarations().all()}
        assert declarations == {
            "ExampleAbstract": "abstract_class",
            "ExampleAnnotation": "annotation",
            "ExampleContract": "interface",
            "ExampleImplementation": "class",
            "ExampleRecord": "record",
            "ExampleStatus": "enum",
        }

    def test_typescript_callable_object_keeps_optional_signature_arguments(self) -> None:
        root = LANGUAGE_EXTENSIONS / "typescript"
        result = self.application.generate_queryable_map("typescript", root, self.scan_policy())
        callback = result.types().where_equal(lambda item: item.item.name, "ExampleCallableObject").first().item
        assert callback.signatures[0].declared_args == 2
        assert callback.signatures[0].optional_args == 1

    def test_python_async_arguments_and_top_level_callable_scope_are_preserved(self) -> None:
        root = LANGUAGE_EXTENSIONS / "python"
        result = self.application.generate_queryable_map("python", root, self.scan_policy())
        asynchronous = result.functions().where_equal(lambda item: item.item.name, "example_async").first().item
        assert asynchronous.declared_args == 2
        assert asynchronous.optional_args == 1
        names = {item.item.qualified_name for item in result.callables().all()}
        assert {"example_async", "example_outer"} <= names
        assert all(item.item.name != "example_inner" for item in result.callables().all())

    def test_typescript_function_alias_retains_the_baseline_type_without_signature_details(self) -> None:
        root = LANGUAGE_EXTENSIONS / "typescript"
        result = self.application.generate_queryable_map("typescript", root, self.scan_policy())
        callback = result.types().where_equal(lambda item: item.item.name, "ExampleCallback").first().item
        assert callback.visibility == "public"
        assert callback.signatures == []

    @pytest.mark.parametrize(
        "convention",
        (
            FixtureLanguageConvention.PYTHON,
            FixtureLanguageConvention.TYPESCRIPT,
            FixtureLanguageConvention.PHP,
        ),
        ids=lambda convention: convention.language,
    )
    def test_module_variable_shape_is_language_neutral(self, convention: FixtureLanguageConvention) -> None:
        root = LANGUAGE_EXTENSIONS / convention.language
        result = self.application.generate_queryable_map(convention.language, root, self.scan_policy())
        variable = (
            result.values()
            .where_equal(lambda item: item.item.name, convention.member_name("example_variable"))
            .first()
            .item
        )
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
