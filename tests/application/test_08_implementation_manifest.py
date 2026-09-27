import hashlib
import json

from modwire.application import DigestAlgorithm, FactCapability

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

        assert manifest.schema_version == 1
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
