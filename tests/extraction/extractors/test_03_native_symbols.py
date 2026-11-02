import re

from modwire.application import CapabilityStatus, FactCapability

from ...support.code_map_fixture.fixture_contract import PolyglotFixtureContract
from ..base_test import ExtractionTestCase

CALL_OCCURRENCE_FIXTURES = ExtractionTestCase.repository / "tests/fixtures/call_occurrences"
LANGUAGE_EXTENSIONS = ExtractionTestCase.repository / "tests/fixtures/code_map/language_extensions"


class TestNativeSymbols(ExtractionTestCase):
    contract = PolyglotFixtureContract(ExtractionTestCase.repository)

    def normalized_name(self, value: str) -> str:
        return re.sub("[^a-z0-9]", "", value.casefold())

    def test_authored_identical_calls_keep_distinct_occurrence_identities(self) -> None:
        languages = self.application.discover(str(CALL_OCCURRENCE_FIXTURES), self.scan_policy())
        assert languages == self.application.extraction.supported_languages()

        for language in languages:
            root = CALL_OCCURRENCE_FIXTURES / language
            first = self.application.generate_queryable_map(language, str(root), self.scan_policy())
            second = self.application.generate_queryable_map(language, str(root), self.scan_policy())

            calls = tuple(
                item.item
                for item in first.calls().all()
                if self.normalized_name(item.item.source_callable_id.qualified_name).endswith("examplecaller")
            )
            assert tuple(item.ordinal for item in calls) == (1, 2)
            assert len({item.identity() for item in calls}) == 2
            assert len({item.source_callable_id.canonical() for item in calls}) == 1
            assert len({item.expression for item in calls}) == 1
            assert first.code_map.to_dict() == second.code_map.to_dict()

    def test_nested_and_constructor_calls_keep_lexical_occurrence_order(self) -> None:
        languages = self.application.discover(str(CALL_OCCURRENCE_FIXTURES), self.scan_policy())
        assert languages == self.application.extraction.supported_languages()

        for language in languages:
            root = CALL_OCCURRENCE_FIXTURES / language
            result = self.application.generate_queryable_map(language, str(root), self.scan_policy())
            calls = tuple(
                item.item
                for item in result.calls().all()
                if self.normalized_name(item.item.source_callable_id.qualified_name).endswith("examplemixedcaller")
            )

            assert tuple(item.ordinal for item in calls) == (1, 2, 3), language
            assert tuple(self.normalized_name(item.target_name) for item in calls) == (
                "exampleouter",
                "exampleinner",
                "examplevalue",
            ), language
            assert len({item.identity() for item in calls}) == 3, language

    def test_native_extractors_preserve_abstract_and_concrete_class_methods(self) -> None:
        for language in self.application.extraction.supported_languages():
            root = LANGUAGE_EXTENSIONS / language
            result = self.application.generate_queryable_map(language, str(root), self.scan_policy())
            abstract = result.abstract_classes().first()
            if abstract is not None:
                declaration = abstract.item
                assert tuple(self.normalized_name(item.name) for item in declaration.abstract_methods) == (
                    self.normalized_name("example_required"),
                ), language
                assert tuple(self.normalized_name(item.name) for item in declaration.methods) == (
                    self.normalized_name("example_concrete"),
                ), language
            else:
                concrete_abstract = result.classes().where_equal(lambda item: item.item.name, "ExampleAbstract").first()
                assert concrete_abstract is not None
                declaration = concrete_abstract.item
                assert declaration.kind is declaration.kind.CLASS, language
                assert {self.normalized_name(item.name) for item in declaration.methods} >= {
                    self.normalized_name("example_required"),
                    self.normalized_name("example_concrete"),
                }, language
            concrete_result = result.classes().where_equal(lambda item: item.item.name, "ExampleImplementation").first()
            assert concrete_result is not None
            concrete = concrete_result.item
            assert self.normalized_name("example_required") in tuple(
                self.normalized_name(item.name) for item in concrete.methods
            ), language

    def test_nullable_class_members_remain_optional_when_the_extractor_publishes_optionality(self) -> None:
        optional_members: list[str] = []
        for language in self.application.extraction.supported_languages():
            root = LANGUAGE_EXTENSIONS / language
            result = self.application.generate_queryable_map(language, str(root), self.scan_policy())
            concrete_result = result.classes().where_equal(lambda item: item.item.name, "ExampleImplementation").first()
            assert concrete_result is not None
            concrete = concrete_result.item
            members = tuple(
                item
                for item in concrete.properties
                if self.normalized_name(item.name) == self.normalized_name("example_optional")
            )
            if not members:
                assert (
                    self.contract.capability_expectation(language, FactCapability.ATTRIBUTES).status
                    is CapabilityStatus.UNSUPPORTED
                ), language
                continue
            assert len(members) == 1, language
            if members[0].is_optional:
                optional_members.append(language)

        assert optional_members

    def test_interfaces_expose_method_signatures(self) -> None:
        interface_languages: list[str] = []
        for language in self.application.extraction.supported_languages():
            root = LANGUAGE_EXTENSIONS / language
            result = self.application.generate_queryable_map(language, str(root), self.scan_policy())
            interfaces = tuple(item.item for item in result.interfaces().all())
            if not interfaces:
                continue
            interface_languages.append(language)
            contracts = tuple(item for item in interfaces if item.name == "ExampleContract")
            assert len(contracts) == 1, language
            assert self.normalized_name(contracts[0].methods[0].name) == self.normalized_name("example_required"), (
                language
            )
            assert len(contracts[0].methods[0].parameters) == 1, language

        assert interface_languages

    def test_java_declaration_forms_use_shared_symbol_families(self) -> None:
        root = LANGUAGE_EXTENSIONS / "java"
        result = self.application.generate_queryable_map("java", str(root), self.scan_policy())
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
        result = self.application.generate_queryable_map("typescript", str(root), self.scan_policy())
        callback_result = result.types().where_equal(lambda item: item.item.name, "ExampleCallableObject").first()
        assert callback_result is not None
        callback = callback_result.item
        assert callback.signatures[0].declared_args == 2
        assert callback.signatures[0].optional_args == 1

    def test_python_async_arguments_and_top_level_callable_scope_are_preserved(self) -> None:
        root = LANGUAGE_EXTENSIONS / "python"
        result = self.application.generate_queryable_map("python", str(root), self.scan_policy())
        asynchronous_result = result.functions().where_equal(lambda item: item.item.name, "example_async").first()
        assert asynchronous_result is not None
        asynchronous = asynchronous_result.item
        assert len(asynchronous.parameters) == 2
        assert sum(parameter.has_default for parameter in asynchronous.parameters) == 1
        names = {item.item.qualified_name for item in result.callables().all()}
        assert {"example_async", "example_outer"} <= names
        assert all(item.item.name != "example_inner" for item in result.callables().all())

    def test_typescript_function_alias_retains_the_baseline_type_without_signature_details(self) -> None:
        root = LANGUAGE_EXTENSIONS / "typescript"
        result = self.application.generate_queryable_map("typescript", str(root), self.scan_policy())
        callback_result = result.types().where_equal(lambda item: item.item.name, "ExampleCallback").first()
        assert callback_result is not None
        callback = callback_result.item
        assert callback.visibility == "public"
        assert callback.signatures == ()

    def test_module_variable_shape_is_language_neutral(self) -> None:
        module_variable_languages: list[str] = []
        for language in self.application.extraction.supported_languages():
            root = LANGUAGE_EXTENSIONS / language
            result = self.application.generate_queryable_map(language, str(root), self.scan_policy())
            variables = tuple(
                item.item
                for item in result.values().all()
                if self.normalized_name(item.item.name) == self.normalized_name("example_variable")
            )
            if not variables:
                continue
            module_variable_languages.append(language)
            assert len(variables) == 1, language
            variable = variables[0]
            constant_result = result.values().where_equal(lambda item: item.item.name, "EXAMPLE_CONSTANT").first()
            assert constant_result is not None
            constant = constant_result.item
            assert variable.scope == constant.scope == "module", language
            assert variable.declaration_kind == "assignment", language
            assert constant.declaration_kind == "constant", language

        assert module_variable_languages
