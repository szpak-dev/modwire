import hashlib
import json

import pytest

from modwire.application import DigestAlgorithm, FactCapability, SourceMemberKind, SourceRelationKind

from .base_test import ApplicationTestCase


class TestImplementationManifest(ApplicationTestCase):
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

        assert manifest.schema_version == 2
        assert manifest.producer.extractor.language == "python"
        assert manifest.producer.extractor.id == "modwire.python.ast"
        assert manifest.producer.modwire_version
        assert {item.capability for item in manifest.producer.capabilities} == set(FactCapability)
        assert manifest.source_manifest.policy == self.scan_policy()
        assert tuple(item.relative_path for item in manifest.source_manifest.sources) == ("src/example.py",)
        assert all(not item.relative_path.startswith("/") for item in manifest.source_manifest.sources)
        assert str(root) not in canonical
        assert "null" not in canonical
        assert any(item.target_reference == "ExampleBase" for item in manifest.inheritance)
        assert any(item.expression == "int" for item in manifest.annotations)
        assert document.format == formats[0]
        assert document.payload == canonical
        assert document.algorithm is DigestAlgorithm.SHA256
        assert document.digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        assert document.verify_digest()
        assert self.application.implementation_manifest(code_map, formats[0]) == document

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
            and item.kind is SourceRelationKind.EXTENDS
            and item.target_reference == "ExampleAbstract"
            for item in manifest.inheritance
        )
        assert tuple(item.specifier for item in manifest.dependencies) == ("abc", "dataclasses", "typing")

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
            (specifier, SourceRelationKind.IMPORTS),
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
            for language in ("python", "typescript", "php")
        }

        vocabularies = {tuple(manifest.model_dump(mode="json")) for manifest in manifests.values()}
        assert len(vocabularies) == 1
        for language, manifest in manifests.items():
            assert manifest.producer.extractor.language == language
            assert manifest.symbols
            assert manifest.callables
            assert manifest.inheritance
            assert {item.capability for item in manifest.producer.capabilities} == set(FactCapability)
