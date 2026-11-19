import shutil
from copy import copy, deepcopy
from dataclasses import replace

import pytest
from pydantic import TypeAdapter, ValidationError

from modwire.application import (
    CodeMap,
    CodeValidationError,
    CodeViolation,
    DeclarationFamily,
    DeclarationIdentity,
    FileId,
    SourceDeclarationScope,
    SourceFile,
    SourceManifest,
    SourceParameter,
    SourceParameterKind,
    SourceParseError,
    SourceScopeKind,
    SourceTypeAbsent,
)

from .base_test import ApplicationTestCase


class TestCodeMapReuse(ApplicationTestCase):
    @pytest.mark.parametrize("language", ("php", "java"))
    def test_native_batch_parse_failure_preserves_diagnostics_and_recovers(self, language: str) -> None:
        root = self.workspace / language
        shutil.copytree(self.repository / f"tests/fixtures/implementation_manifest/{language}/canonical/src", root)
        broken = self.repository / f"tests/fixtures/code_map_reuse/native_failure/{language}/Broken.{language}"
        target = root / broken.name
        shutil.copyfile(broken, target)

        with pytest.raises(SourceParseError) as raised:
            self.application.generate_map(language, str(root), self.scan_policy())

        assert raised.value.language == language
        assert raised.value.line >= 1
        assert raised.value.column >= 1
        target.unlink()
        recovered = self.application.generate_map(language, str(root), self.scan_policy())
        assert tuple(recovered.extraction.files) == (f"Example.{language}",)

    @pytest.mark.parametrize("line_ending", (b"\n", b"\r\n", b"\r"))
    def test_java_preserves_utf8_block_offsets_after_multibyte_text(self, line_ending: bytes) -> None:
        fixture = self.repository / "tests/fixtures/code_map_reuse/java/Example.java"
        root = self.workspace / "example-java"
        root.mkdir()
        content = fixture.read_bytes().replace(b"\n", line_ending)
        (root / "Example.java").write_bytes(content)

        source = self.application.generate_map("java", str(root), self.scan_policy()).extraction.files[
            FileId("Example.java")
        ]
        value = next(item for item in source.values if item.name == "exampleValue")
        scope = value.placement.lexical_scope
        assert scope.kind is SourceScopeKind.BLOCK
        expected_start = content.index(b"{", content.index(b"if"))
        assert scope.start_utf8_offset == expected_start
        assert scope.end_utf8_offset == content.index(b"}", expected_start) + 1

    @pytest.mark.parametrize("reference", (-1, 0, True, 0.5))
    def test_public_documents_reject_internal_value_references(self, reference: object) -> None:
        with pytest.raises(ValidationError):
            SourceParameter.model_validate(
                {"name": "example", "type": reference, "kind": SourceParameterKind.POSITIONAL}
            )

    def test_type_slot_still_accepts_an_omitted_absent_discriminator(self) -> None:
        parameter = SourceParameter.model_validate(
            {"name": "example", "type": {}, "kind": SourceParameterKind.POSITIONAL}
        )

        assert parameter.type == SourceTypeAbsent()

    @pytest.mark.parametrize("line_ending", (b"\n", b"\r\n", b"\r"))
    def test_ruby_preserves_line_counts_for_each_line_ending(self, line_ending: bytes) -> None:
        fixture = self.repository / "tests/fixtures/code_map_reuse/ruby_lines/example.rb"
        root = self.workspace / "example-ruby"
        root.mkdir()
        (root / "example.rb").write_bytes(fixture.read_bytes().replace(b"\n", line_ending))

        source = self.application.generate_map("ruby", str(root), self.scan_policy()).extraction.files[
            FileId("example.rb")
        ]

        assert source.line_count == 4
        assert source.code_line_count == 0

    def test_ruby_keeps_imports_and_calls_in_their_authored_scopes(self) -> None:
        root = self.repository / "tests/fixtures/code_map_reuse/ruby"
        source = self.application.generate_map("ruby", str(root), self.scan_policy()).extraction.files[
            FileId("example.rb")
        ]

        assert [item.path for item in source.imports] == [
            "example/root",
            "example/default",
            "example/local",
            "example/lambda-default",
        ]
        assert [
            item.target_name
            for item in source.calls
            if item.source_callable_id.qualified_name == "Example.Owner.example_outer"
        ] == ["require_relative", "example_call", "each", "example_items"]
        assert [
            item.target_name
            for item in source.calls
            if item.source_callable_id.qualified_name == "Example.Owner.example_outer.example_proc"
        ] == ["example_lambda_call"]
        assert [
            item.target_name
            for item in source.calls
            if item.source_callable_id.qualified_name == "Example.Owner.example_inner"
        ] == ["example_inner_call"]
        anonymous = source.anonymous_callables[0]
        assert [item.target_name for item in source.calls if item.source_callable_id == anonymous.declaration_id] == [
            "example_block_call"
        ]
        owner = next(item for item in source.declarations if item.name == "Example.Owner")
        assert [item.name for item in owner.properties] == ["example_value"]

    def test_editing_supplied_fields_does_not_change_another_declaration(self) -> None:
        root = self.repository / "tests/fixtures/code_map_reuse/python"
        source = self.application.generate_map("python", str(root), self.scan_policy()).extraction.files[
            FileId("example.py")
        ]
        first, second = source.functions
        original = first.model_dump_json()
        fields = first.model_fields_set

        fields.remove("docstring")

        assert "docstring" not in first.model_dump(exclude_unset=True)
        assert "docstring" in second.model_dump(exclude_unset=True)
        assert first.model_dump_json() == original
        assert first.model_fields_set is fields
        fields.add("docstring")
        assert "docstring" in first.model_dump(exclude_unset=True)

    @pytest.mark.parametrize("inspect_before_copy", (False, True))
    def test_copies_keep_independent_supplied_fields(self, inspect_before_copy: bool) -> None:
        root = self.repository / "tests/fixtures/code_map_reuse/python"
        source = self.application.generate_map("python", str(root), self.scan_policy()).extraction.files[
            FileId("example.py")
        ]
        function = source.functions[0]
        if inspect_before_copy:
            assert "docstring" in function.model_fields_set
        copies = (copy(function), deepcopy(function), function.model_copy(), function.model_copy(deep=True))

        for copied in copies:
            copied.model_fields_set.remove("docstring")

        assert "docstring" in function.model_dump(exclude_unset=True)
        for copied in copies:
            assert "docstring" not in copied.model_dump(exclude_unset=True)
            changed = copied.model_copy(update={"docstring": ""})
            assert "docstring" in changed.model_dump(exclude_unset=True)
            assert "docstring" not in copied.model_dump(exclude_unset=True)

    def test_omitted_and_explicit_defaults_keep_distinct_serialization(self) -> None:
        omitted = SourceParameter(name="example", type=SourceTypeAbsent(), kind=SourceParameterKind.POSITIONAL)
        explicit = SourceParameter(
            name="example", type=SourceTypeAbsent(), kind=SourceParameterKind.POSITIONAL, has_default=False
        )

        assert omitted == explicit
        assert omitted.model_dump_json() == explicit.model_dump_json()
        assert "has_default" not in omitted.model_dump(exclude_unset=True)
        assert explicit.model_dump(exclude_unset=True)["has_default"] is False
        changed = omitted.model_copy(update={"has_default": False})
        assert changed.model_dump(exclude_unset=True)["has_default"] is False
        assert "has_default" not in omitted.model_dump(exclude_unset=True)

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
        restored = TypeAdapter(DeclarationIdentity).validate_json(TypeAdapter(DeclarationIdentity).dump_json(identity))
        changed = replace(identity, ordinal=identity.ordinal + 1)
        identities = {identity: "original", changed: "changed"}

        assert hash(identity) == hash(restored)
        assert identities[restored] == "original"
        assert identities[changed] == "changed"
        assert changed.canonical() != identity.canonical()

    @pytest.mark.parametrize("deep", (False, True))
    @pytest.mark.parametrize(
        ("field", "value"),
        (
            ("source_id", "example-other.py"),
            ("family", DeclarationFamily.TYPE),
            ("qualified_name", "example.other"),
            ("ordinal", 9999),
            ("content_digest", "1" * 64),
        ),
    )
    def test_copied_identity_retains_hash_lookup_after_each_field_changes(
        self, field: str, value: object, deep: bool
    ) -> None:
        root = self.repository / "tests/fixtures/code_map_reuse/python"
        source = self.application.generate_map("python", str(root), self.scan_policy()).extraction.files[
            FileId("example.py")
        ]
        identity = source.functions[0].declaration_id
        original = {identity: "original"}

        changed = replace(deepcopy(identity) if deep else copy(identity), **{field: value})
        restored = TypeAdapter(DeclarationIdentity).validate_json(TypeAdapter(DeclarationIdentity).dump_json(changed))

        assert changed != identity
        assert {changed: "changed"}[restored] == "changed"
        assert restored not in original
        assert original[identity] == "original"

    @pytest.mark.parametrize("self_cycle", (False, True))
    def test_external_document_rejects_cyclic_lexical_ownership(self, self_cycle: bool) -> None:
        root = self.repository / "tests/fixtures/code_map_reuse/python"
        source = self.application.generate_map("python", str(root), self.scan_policy()).extraction.files[
            FileId("example.py")
        ]
        first, second = source.functions
        first_scope = SourceDeclarationScope(
            declaration_id=first.declaration_id if self_cycle else second.declaration_id
        )
        second_scope = SourceDeclarationScope(declaration_id=first.declaration_id)
        changed = source.model_copy(
            update={
                "functions": (
                    first.model_copy(
                        update={"placement": first.placement.model_copy(update={"lexical_scope": first_scope})}
                    ),
                    second.model_copy(
                        update={"placement": second.placement.model_copy(update={"lexical_scope": second_scope})}
                    ),
                )
            }
        )

        with pytest.raises(CodeValidationError) as raised:
            SourceFile.model_validate_json(changed.to_json())

        assert raised.value.violation is CodeViolation.CYCLIC_LEXICAL_SCOPE

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
            update={"declaration_id": replace(function.declaration_id, content_digest="0" * 64)}
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
