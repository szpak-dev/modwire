import pytest

from modwire.application import CodeMap, CodeValidationError, CodeViolation, DeclarationIdentity, SourceManifest

from .base_test import ApplicationTestCase


class TestCodeMapReuse(ApplicationTestCase):
    def test_external_manifest_rejects_a_changed_digest(self) -> None:
        root = self.repository / "tests/fixtures/code_map_reuse/python"
        manifest = self.application.generate_map("python", str(root), self.scan_policy()).extraction.manifest
        changed = manifest.model_copy(update={"digest": "0" * 64})

        with pytest.raises(CodeValidationError) as raised:
            SourceManifest.model_validate_json(changed.to_json())

        assert raised.value.violation is CodeViolation.INVALID_SOURCE_MANIFEST_DIGEST

    def test_external_manifest_rejects_duplicate_source_identity(self) -> None:
        root = self.repository / "tests/fixtures/code_map_reuse/python"
        manifest = self.application.generate_map("python", str(root), self.scan_policy()).extraction.manifest
        changed = manifest.model_copy(update={"sources": (manifest.sources[0], manifest.sources[0])})

        with pytest.raises(CodeValidationError) as raised:
            SourceManifest.model_validate_json(changed.to_json())

        assert raised.value.violation is CodeViolation.DUPLICATE_SOURCE_IDENTITY

    def test_external_manifest_rejects_noncanonical_source_order(self) -> None:
        root = self.repository / "tests/fixtures/code_map_reuse/python"
        manifest = self.application.generate_map("python", str(root), self.scan_policy()).extraction.manifest
        changed = manifest.model_copy(update={"sources": tuple(reversed(manifest.sources))})

        with pytest.raises(CodeValidationError) as raised:
            SourceManifest.model_validate_json(changed.to_json())

        assert raised.value.violation is CodeViolation.NON_CANONICAL_SOURCE_ARTIFACTS

    def test_identity_hashing_tracks_value_equality_and_copies(self) -> None:
        root = self.repository / "tests/fixtures/code_map_reuse/python"
        code_map = self.application.generate_map("python", str(root), self.scan_policy())
        source = next(iter(code_map.extraction.files.values()))
        identity = source.functions[0].declaration_id
        restored = DeclarationIdentity.model_validate_json(identity.to_json())
        changed = identity.model_copy(update={"ordinal": identity.ordinal + 1})
        identities = {identity: "original", changed: "changed"}

        assert hash(identity) == hash(restored)
        assert identities[restored] == "original"
        assert identities[changed] == "changed"
        assert changed.canonical() != identity.canonical()

    @pytest.mark.parametrize("deep", (False, True))
    def test_structural_copies_observe_their_own_callables_and_placements(self, deep: bool) -> None:
        root = self.repository / "tests/fixtures/code_map_reuse/python"
        code_map = self.application.generate_map("python", str(root), self.scan_policy())
        source = next(iter(code_map.extraction.files.values()))
        original_callables = source.canonical_callables()
        original_placements = source.declaration_placements()

        changed = source.model_copy(update={"functions": source.functions[1:]}, deep=deep)
        emptied = changed.model_copy(update={"functions": ()}, deep=deep)

        assert tuple(item.name for item in changed.canonical_callables()) == ("second",)
        assert tuple(identity.qualified_name for identity, _ in changed.declaration_placements()) == ("second",)
        assert emptied.canonical_callables() == ()
        assert emptied.declaration_placements() == ()
        assert source.canonical_callables() == original_callables
        assert source.declaration_placements() == original_placements

    def test_external_documents_still_reject_foreign_capture_identity(self) -> None:
        root = self.repository / "tests/fixtures/code_map_reuse/python"
        code_map = self.application.generate_map("python", str(root), self.scan_policy())
        source_id, source = next(iter(code_map.extraction.files.items()))
        function = source.functions[0]
        changed_function = function.model_copy(
            update={"declaration_id": function.declaration_id.model_copy(update={"content_digest": "0" * 64})}
        )
        changed_source = source.model_copy(update={"functions": (changed_function,), "exports": []})
        changed = code_map.model_copy(
            update={
                "extraction": code_map.extraction.model_copy(
                    update={"files": code_map.extraction.files | {source_id: changed_source}}
                )
            }
        )

        with pytest.raises(CodeValidationError) as raised:
            CodeMap.model_validate_json(changed.to_json())

        assert raised.value.violation is CodeViolation.INCONSISTENT_DECLARATION_CAPTURE

    @pytest.mark.parametrize("language", ("python", "typescript", "php", "java", "ruby"))
    def test_derived_views_do_not_change_the_public_document(self, language: str) -> None:
        root = self.repository / "tests/fixtures/implementation_manifest" / language / "no_calls/src"
        code_map = self.application.generate_map(language, str(root), self.scan_policy())
        original = code_map.to_json()
        for source in code_map.extraction.files.values():
            source.canonical_callables()
            source.declaration_placements()

        assert code_map.to_json() == original
        assert CodeMap.model_validate_json(original) == code_map
