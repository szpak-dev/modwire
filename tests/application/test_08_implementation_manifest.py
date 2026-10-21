import hashlib
import json

import pytest

from modwire.application import (
    CapabilityStatus,
    CodeMap,
    CodeValidationError,
    DigestAlgorithm,
    FactCapability,
    RelationshipFamily,
    SourceCallResolution,
    SourceDeclarationRelationKind,
    SourceDependencyKind,
    SourceMemberKind,
)

from ..support.code_map import CodeMapFactory
from .base_test import ApplicationTestCase


class TestImplementationManifest(ApplicationTestCase):
    def test_public_code_map_rejects_a_non_value_symbol_kind_without_changing_valid_input(self) -> None:
        code_map = (
            CodeMapFactory()
            .queryable(
                {
                    "example.source": {
                        "values": [
                            CodeMapFactory().source_value(
                                "example_value",
                                declaration_kind="assignment",
                                scope="module",
                            )
                        ]
                    }
                },
                (),
            )
            .code_map
        )
        before = code_map.to_json()
        invalid = before.replace('"value_kind": "value_literal"', '"value_kind": "class"', 1)

        with pytest.raises(CodeValidationError) as raised:
            CodeMap.model_validate_json(invalid)

        assert raised.value.subject == "example_value"
        assert code_map.to_json() == before
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(code_map, format)
        )
        assert tuple(item.kind for item in manifest.symbols) == ("value_literal",)

    def test_public_manifest_uses_one_authored_namespace_across_multiple_sources(self) -> None:
        namespace = {"kind": "namespace", "qualified_name": "Example.Shared"}
        code_map = (
            CodeMapFactory()
            .queryable(
                {
                    "example_first.source": {
                        "namespaces": [namespace],
                        "declarations": [
                            CodeMapFactory().source_class("ExampleFirst", line_count=1, methods=(), properties=())
                        ],
                    },
                    "example_second.source": {
                        "namespaces": [namespace],
                        "declarations": [
                            CodeMapFactory().source_class("ExampleSecond", line_count=1, methods=(), properties=())
                        ],
                    },
                },
                (),
            )
            .code_map
        )
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(code_map, format)
        )

        assert tuple(item.qualified_name for item in manifest.namespaces) == ("Example.Shared",)
        assert {item.qualified_name for item in manifest.symbols} == {
            "Example.Shared.ExampleFirst",
            "Example.Shared.ExampleSecond",
        }

    def test_public_manifest_serializes_closed_vocabularies_as_exact_strings(self) -> None:
        root = self.project(
            {
                "src/example.py": (
                    "from example_external import ExampleExternal\n\n"
                    "class ExampleValue:\n"
                    "    example_name: str\n\n"
                    "    @example_decorator\n"
                    "    def execute(self, example_input: int = 1) -> str:\n"
                    "        return str(example_input)\n"
                )
            }
        )
        format = self.application.implementation_manifest_formats()[0]
        document = self.application.implementation_manifest(
            self.application.generate_map("python", root, self.scan_policy()), format
        )
        payload = json.loads(document.payload)

        assert payload["source_manifest"]["digest_algorithm"] == "sha256"
        assert {item["kind"] for item in payload["symbols"]} == {"callable", "class"}
        assert {item["visibility"] for item in payload["symbols"]} == {"public"}
        assert {item["callable_kind"] for item in payload["callables"]} == {"instance_method"}
        assert {item["kind"] for item in payload["parameters"]} == {"positional"}
        assert {item["role"] for item in payload["annotations"]} == {
            "attribute_type",
            "decorator",
            "parameter_type",
            "return_type",
        }
        assert {(item["target_kind"], item["resolution"]) for item in payload["dependencies"]} == {
            ("external", "external")
        }

    def test_public_manifest_is_canonical_complete_and_provenance_bearing(self) -> None:
        root = self.project(
            {
                "src/example.py": (
                    "class ExampleBase:\n"
                    "    pass\n\n"
                    "class ExampleChild(ExampleBase):\n"
                    "    def execute(self, value: int = 1) -> str:\n"
                    "        return str(value)\n"
                )
            }
        )

        code_map = self.application.generate_map("python", root, self.scan_policy())
        formats = self.application.implementation_manifest_formats()
        assert tuple(format.id for format in formats) == ("canonical-json",)

        document = self.application.implementation_manifest(code_map, formats[0])
        manifest = self.application.read_implementation_manifest(document)
        canonical = json.dumps(
            manifest.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        assert manifest.schema_version == 8
        assert manifest.producer.extractor.language == "python"
        assert manifest.producer.extractor.id == "modwire.python.ast"
        assert manifest.producer.modwire_version
        assert {item.capability for item in manifest.producer.capabilities} == set(FactCapability)
        assert manifest.source_manifest.policy == self.scan_policy()
        assert tuple(item.relative_path for item in manifest.source_manifest.sources) == ("src/example.py",)
        assert all(not item.relative_path.startswith("/") for item in manifest.source_manifest.sources)
        assert str(root) not in canonical
        assert any(item.target_reference == "ExampleBase" for item in manifest.declaration_relations)
        assert any(item.expression == "int" for item in manifest.annotations)
        assert document.format == formats[0]
        assert document.payload == canonical
        assert document.algorithm is DigestAlgorithm.SHA256
        assert document.digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        assert document.verify_digest()
        assert self.application.implementation_manifest(code_map, formats[0]) == document

    def test_public_map_and_manifest_publish_the_same_observed_call(self) -> None:
        root = self.project(
            {
                "src/example.py": (
                    "def example_target():\n    return 1\n\ndef example_caller():\n    return example_target()\n"
                )
            }
        )
        code_map = self.application.generate_queryable_map("python", root, self.scan_policy())
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(code_map.code_map, format)
        )

        calls = tuple(result.item for result in code_map.calls().all())
        assert len(calls) == 1
        assert len(manifest.calls) == 1
        assert manifest.calls[0].source_id == calls[0].source_id
        assert manifest.calls[0].line == calls[0].line
        assert manifest.calls[0].expression == calls[0].expression
        assert manifest.calls[0].target_name == calls[0].target_name == "example_target"
        assert manifest.calls[0].resolution is calls[0].resolution is SourceCallResolution.RESOLVED
        callable_ids = {item.symbol_id.canonical() for item in manifest.callables}
        assert manifest.calls[0].source_callable_id.canonical() in callable_ids
        assert manifest.calls[0].target_callable_id is not None
        assert manifest.calls[0].target_callable_id.canonical() in callable_ids

    def test_supported_member_inventory_truthfully_publishes_no_observed_calls(self) -> None:
        root = self.project({"src/example.py": "def example_value():\n    return 1\n"})
        code_map = self.application.generate_queryable_map("python", root, self.scan_policy())
        member = next(
            coverage
            for coverage in code_map.code_map.producer.relationship_capabilities
            if coverage.family is RelationshipFamily.MEMBER
        )
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(code_map.code_map, format)
        )

        assert member.inventory is CapabilityStatus.SUPPORTED
        assert FactCapability.CALLS in member.evidence_requirements
        assert code_map.calls().all() == ()
        assert manifest.calls == ()

    def test_python_manifest_publishes_complete_class_facts(self) -> None:
        root = self.project(
            {
                "src/example.py": (
                    "from abc import ABC, abstractmethod\n\n"
                    "from dataclasses import dataclass\n"
                    "from typing import ClassVar\n\n"
                    "@example_contract\n"
                    "class ExampleAbstract(ABC):\n"
                    "    example_shared: str = 'example'\n\n"
                    "    @abstractmethod\n"
                    "    def example_required(self) -> str:\n"
                    "        raise NotImplementedError\n\n"
                    "@example_value('example')\n"
                    "class ExampleValue(ExampleAbstract):\n"
                    "    __example_static: ClassVar[str] = 'example'\n"
                    "    EXAMPLE_LIMIT = 1\n"
                    "    example_name: str\n\n"
                    "    def __init__(self, example_optional: str | None = None):\n"
                    "        self.example_optional: str | None = example_optional\n\n"
                    "    def example_required(self) -> str:\n"
                    "        return 'example'\n"
                    "\n"
                    "@dataclass\n"
                    "class ExampleData:\n"
                    "    example_field: str\n"
                )
            }
        )
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map("python", root, self.scan_policy()), format
            )
        )
        symbol_ids = {item.id.qualified_name: item.id for item in manifest.symbols}
        value_id = symbol_ids["ExampleValue"]
        attributes = {item.name: item for item in manifest.attributes if item.owner_symbol_id == value_id}
        abstract_attributes = {
            item.name: item for item in manifest.attributes if item.owner_symbol_id == symbol_ids["ExampleAbstract"]
        }
        data_attributes = {
            item.name: item for item in manifest.attributes if item.owner_symbol_id == symbol_ids["ExampleData"]
        }

        assert attributes["__example_static"].id == (f"{value_id.canonical()}::attribute:__example_static")
        assert attributes["__example_static"].annotation == "ClassVar[str]"
        assert attributes["__example_static"].visibility == "private"
        assert attributes["__example_static"].member_kind is SourceMemberKind.STATIC
        assert attributes["EXAMPLE_LIMIT"].annotation == ""
        assert attributes["EXAMPLE_LIMIT"].member_kind is SourceMemberKind.STATIC
        assert attributes["example_name"].annotation == "str"
        assert not attributes["example_name"].is_optional
        assert attributes["example_name"].member_kind is SourceMemberKind.INSTANCE
        assert attributes["example_optional"].annotation == "str | None"
        assert attributes["example_optional"].is_optional
        assert attributes["example_optional"].member_kind is SourceMemberKind.INSTANCE
        assert abstract_attributes["example_shared"].annotation == "str"
        assert abstract_attributes["example_shared"].member_kind is SourceMemberKind.INSTANCE
        assert data_attributes["example_field"].annotation == "str"
        assert data_attributes["example_field"].member_kind is SourceMemberKind.INSTANCE
        assert {(item.target_id, item.role, item.expression) for item in manifest.annotations} >= {
            (symbol_ids["ExampleAbstract"].canonical(), "declaration", "example_contract"),
            (value_id.canonical(), "declaration", "example_value('example')"),
            (attributes["example_optional"].id, "attribute_type", "str | None"),
        }
        assert any(
            item.source_symbol_id == value_id
            and item.kind is SourceDeclarationRelationKind.EXTENDS
            and item.target_reference == "ExampleAbstract"
            for item in manifest.declaration_relations
        )
        assert tuple(item.specifier for item in manifest.dependencies) == ("abc", "dataclasses", "typing")

    def test_python_manifest_does_not_misclassify_public_functions_or_method_names_as_properties(self) -> None:
        root = self.project(
            {
                "src/example.py": (
                    "@property\n"
                    "def example_label() -> str:\n"
                    "    return 'example'\n\n"
                    "class ExampleValue:\n"
                    "    @example_decorator\n"
                    "    def property(self) -> str:\n"
                    "        return 'example'\n"
                )
            }
        )
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map("python", root, self.scan_policy()), format
            )
        )

        assert {item.symbol_id.qualified_name for item in manifest.callables} >= {
            "example_label",
            "ExampleValue.property",
        }
        assert not manifest.attributes

    def test_python_manifest_preserves_property_annotation_boundaries(self) -> None:
        root = self.project(
            {
                "src/example.py": (
                    "class ExampleValue:\n"
                    "    @property\n"
                    "    def example_optional(self) -> str | None:\n"
                    "        return None\n\n"
                    "    @property\n"
                    "    def example_untyped(self):\n"
                    "        return 'example'\n"
                )
            }
        )
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map("python", root, self.scan_policy()), format
            )
        )
        attributes = {item.name: item for item in manifest.attributes}

        assert attributes["example_optional"].annotation == "str | None"
        assert attributes["example_optional"].is_optional
        assert attributes["example_untyped"].annotation == ""
        assert not attributes["example_untyped"].is_optional

    def test_python_manifest_publishes_strenum_members_as_string_attributes(self) -> None:
        root = self.project(
            {
                "src/example.py": (
                    "from enum import StrEnum\n\nclass ExampleKind(StrEnum):\n    EXAMPLE_VALUE = 'example'\n"
                )
            }
        )
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map("python", root, self.scan_policy()), format
            )
        )
        kind_id = next(item.id for item in manifest.symbols if item.id.qualified_name == "ExampleKind")
        attribute = next(item for item in manifest.attributes if item.owner_symbol_id == kind_id)

        assert attribute.name == "EXAMPLE_VALUE"
        assert attribute.annotation == "str"
        assert attribute.member_kind is SourceMemberKind.STATIC
        assert (attribute.id, "attribute_type", "str") in {
            (item.target_id, item.role, item.expression) for item in manifest.annotations
        }

    def test_python_manifest_projects_properties_as_attributes(self) -> None:
        root = self.project(
            {
                "src/example.py": (
                    "class ExampleValue:\n    @property\n    def example_name(self) -> str:\n        return 'example'\n"
                )
            }
        )
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map("python", root, self.scan_policy()), format
            )
        )
        value_id = next(item.id for item in manifest.symbols if item.id.qualified_name == "ExampleValue")
        attribute = next(
            item for item in manifest.attributes if item.owner_symbol_id == value_id and item.name == "example_name"
        )

        assert attribute.annotation == "str"
        assert not attribute.is_optional
        assert attribute.member_kind is SourceMemberKind.INSTANCE
        assert not any(item.symbol_id.qualified_name == "ExampleValue.example_name" for item in manifest.callables)
        assert not any(item.id.qualified_name == "ExampleValue.example_name" for item in manifest.symbols)
        assert (attribute.id, "attribute_type", "str") in {
            (item.target_id, item.role, item.expression) for item in manifest.annotations
        }

    def test_typescript_manifest_distinguishes_undefined_value_types_from_optional_properties(self) -> None:
        root = self.project(
            {
                "src/example.ts": (
                    "@exampleDecorator('example')\n"
                    "class ExampleValue {\n"
                    "    example_required: undefined[] = [];\n"
                    "    example_optional: string | undefined;\n"
                    "}\n\n"
                    "interface ExampleContract {\n"
                    "    example_required: undefined[];\n"
                    "    example_optional: string | undefined;\n"
                    "}\n\n"
                    "type ExampleShape = {\n"
                    "    example_required: undefined[];\n"
                    "    example_optional: string | undefined;\n"
                    "};\n"
                )
            }
        )
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map("typescript", root, self.scan_policy()), format
            )
        )
        symbol_ids = {item.id.qualified_name: item.id for item in manifest.symbols}

        for owner_name in ("ExampleValue", "ExampleContract", "ExampleShape"):
            owner_attributes = {
                item.name: item for item in manifest.attributes if item.owner_symbol_id == symbol_ids[owner_name]
            }
            assert not owner_attributes["example_required"].is_optional
            assert owner_attributes["example_required"].annotation == "undefined[]"
            assert owner_attributes["example_optional"].is_optional
            assert owner_attributes["example_optional"].annotation == "string | undefined"
        assert any(
            item.target_id == symbol_ids["ExampleValue"].canonical()
            and item.role == "declaration"
            and item.expression == "exampleDecorator('example')"
            for item in manifest.annotations
        )

    def test_php_manifest_preserves_qualified_dnf_types_and_attributes(self) -> None:
        root = self.project(
            {
                "src/example.php": (
                    "<?php\n"
                    "#[\\Example\\Attribute(name: 'example')]\n"
                    "class ExampleValue {\n"
                    "    public static string $example_static = 'example';\n"
                    "    protected (\\Example\\FirstType&\\Example\\SecondType)|null $example_value = null;\n"
                    "}\n"
                )
            }
        )
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map("php", root, self.scan_policy()), format
            )
        )
        value_id = next(item.id for item in manifest.symbols if item.id.qualified_name == "ExampleValue")
        attributes = {item.name: item for item in manifest.attributes if item.owner_symbol_id == value_id}

        assert attributes["example_static"].annotation == "string"
        assert attributes["example_static"].visibility == "public"
        assert attributes["example_static"].member_kind is SourceMemberKind.STATIC
        assert attributes["example_value"].annotation == ("(\\Example\\FirstType&\\Example\\SecondType)|null")
        assert attributes["example_value"].visibility == "protected"
        assert attributes["example_value"].is_optional
        assert attributes["example_value"].member_kind is SourceMemberKind.INSTANCE
        assert any(
            item.target_id == value_id.canonical()
            and item.role == "declaration"
            and item.expression == "\\Example\\Attribute(name: 'example')"
            for item in manifest.annotations
        )

    @pytest.mark.parametrize(
        ("language", "path", "content", "specifier"),
        (
            ("python", "src/example.py", "from .example_value import ExampleValue\n", ".example_value"),
            (
                "typescript",
                "src/example.ts",
                "import { ExampleValue } from './example-value';\n",
                "./example-value",
            ),
            (
                "php",
                "src/example.php",
                "<?php\nuse \\Example\\ExampleValue;\n",
                "\\Example\\ExampleValue",
            ),
        ),
    )
    def test_manifest_dependencies_preserve_authored_specifiers(
        self, language: str, path: str, content: str, specifier: str
    ) -> None:
        root = self.project({path: content})
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(
                self.application.generate_map(language, root, self.scan_policy()), format
            )
        )

        assert tuple((item.specifier, item.kind) for item in manifest.dependencies) == (
            (specifier, SourceDependencyKind.IMPORTS),
        )

    def test_source_edit_changes_both_source_and_implementation_identity(self) -> None:
        root = self.project({"src/example.py": "def example() -> int:\n    return 1\n"})
        format = self.application.implementation_manifest_formats()[0]

        before_document = self.application.implementation_manifest(
            self.application.generate_map("python", root, self.scan_policy()), format
        )
        (root / "src/example.py").write_text("def example() -> int:\n    return 2\n", encoding="utf-8")
        after_document = self.application.implementation_manifest(
            self.application.generate_map("python", root, self.scan_policy()), format
        )
        before = self.application.read_implementation_manifest(before_document)
        after = self.application.read_implementation_manifest(after_document)

        assert before.source_manifest.digest != after.source_manifest.digest
        assert before_document.digest != after_document.digest

    def test_supported_languages_publish_one_manifest_vocabulary(self) -> None:
        root = self.project(
            {
                "src/example.py": (
                    "class ExampleBase:\n"
                    "    pass\n\n"
                    "class ExampleChild(ExampleBase):\n"
                    "    def execute(self, value: int = 1) -> str:\n"
                    "        return str(value)\n"
                ),
                "src/example.ts": (
                    "class ExampleBase {}\n"
                    "class ExampleChild extends ExampleBase {\n"
                    "    execute(value: number = 1): string { return String(value); }\n"
                    "}\n"
                ),
                "src/ExampleChild.java": (
                    "class ExampleBase {}\n"
                    "class ExampleChild extends ExampleBase {\n"
                    "    String execute(int value) { return String.valueOf(value); }\n"
                    "}\n"
                ),
                "src/example.php": (
                    "<?php\n"
                    "class ExampleBase {}\n"
                    "class ExampleChild extends ExampleBase {\n"
                    "    public function execute(int $value = 1): string { return (string) $value; }\n"
                    "}\n"
                ),
            }
        )
        format = self.application.implementation_manifest_formats()[0]
        manifests = {
            language: self.application.read_implementation_manifest(
                self.application.implementation_manifest(
                    self.application.generate_map(language, root, self.scan_policy()), format
                )
            )
            for language in ("python", "typescript", "php", "java")
        }

        vocabularies = {tuple(manifest.model_dump(mode="json")) for manifest in manifests.values()}
        assert len(vocabularies) == 1
        for language, manifest in manifests.items():
            assert manifest.producer.extractor.language == language
            assert manifest.producer.extractor.version
            assert manifest.symbols
            assert manifest.callables
            assert manifest.declaration_relations
            assert {item.capability for item in manifest.producer.capabilities} == set(FactCapability)
            assert {item.family for item in manifest.producer.relationship_capabilities} == set(RelationshipFamily)
            member = next(
                coverage
                for coverage in manifest.producer.relationship_capabilities
                if coverage.family is RelationshipFamily.MEMBER
            )
            assert FactCapability.CALLS in member.evidence_requirements
