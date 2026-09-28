import pytest
from pydantic import ValidationError

from modwire.application import SourceManifestIdentity

from .base_test import ApplicationTestCase


class TestSourceManifestIdentity(ApplicationTestCase):
    @pytest.mark.parametrize(
        ("language", "source_path", "before", "after"),
        (
            ("python", "src/example.py", "example = 1\n", "example = 2\n"),
            ("typescript", "src/example.ts", "export const example = 1;\n", "export const example = 2;\n"),
            ("php", "src/example.php", "<?php\n$example = 1;\n", "<?php\n$example = 2;\n"),
        ),
    )
    def test_current_identity_matches_the_observed_manifest_and_tracks_content_changes(
        self,
        language: str,
        source_path: str,
        before: str,
        after: str,
    ) -> None:
        root = self.project({source_path: before})
        policy = self.scan_policy()
        code_map = self.application.generate_map(language, root, policy)
        format = self.application.implementation_manifest_formats()[0]
        manifest = self.application.read_implementation_manifest(
            self.application.implementation_manifest(code_map, format)
        )

        identity = self.application.source_manifest_identity(language, root, policy)

        assert identity.digest_algorithm == manifest.source_manifest.digest_algorithm
        assert identity.digest == manifest.source_manifest.digest

        (root / source_path).write_text(after, encoding="utf-8")

        assert self.application.source_manifest_identity(language, root, policy) != identity

    def test_added_source_changes_the_current_identity(self) -> None:
        root = self.project({"src/example.py": "example = 1\n"})
        before = self.application.source_manifest_identity("python", root, self.scan_policy())

        (root / "src/added.py").write_text("added = 1\n", encoding="utf-8")

        assert self.application.source_manifest_identity("python", root, self.scan_policy()) != before

    def test_removed_source_changes_the_current_identity(self) -> None:
        root = self.project({"src/example.py": "example = 1\n", "src/removed.py": "removed = 1\n"})
        before = self.application.source_manifest_identity("python", root, self.scan_policy())

        (root / "src/removed.py").unlink()

        assert self.application.source_manifest_identity("python", root, self.scan_policy()) != before

    def test_renamed_source_changes_the_current_identity(self) -> None:
        root = self.project({"src/example.py": "example = 1\n"})
        before = self.application.source_manifest_identity("python", root, self.scan_policy())

        (root / "src/example.py").rename(root / "src/renamed.py")

        assert self.application.source_manifest_identity("python", root, self.scan_policy()) != before

    def test_excluded_source_changes_the_current_identity(self) -> None:
        root = self.project({"src/example.py": "example = 1\n", "src/excluded.py": "excluded = 1\n"})
        before = self.application.source_manifest_identity("python", root, self.scan_policy())
        policy = self.configured_scan_policy(("src/excluded.py",), False)

        after = self.application.source_manifest_identity("python", root, policy)

        assert after != before

    def test_change_beneath_an_excluded_directory_does_not_change_the_identity(self) -> None:
        root = self.project({"src/example.py": "example = 1\n", "generated/example.py": "generated = 1\n"})
        policy = self.configured_scan_policy(("generated/**",), False)
        before = self.application.source_manifest_identity("python", root, policy)

        (root / "generated/example.py").write_text("generated = 2\n", encoding="utf-8")

        assert self.application.source_manifest_identity("python", root, policy) == before

    @pytest.mark.parametrize(
        ("language", "source_path", "content"),
        (
            ("python", "src/example.py", "def invalid(:\n"),
            ("typescript", "src/example.ts", "export const = ;\n"),
            ("php", "src/example.php", "<?php\nfunction invalid( {\n"),
        ),
    )
    def test_invalid_source_syntax_does_not_invoke_the_parser(
        self, language: str, source_path: str, content: str
    ) -> None:
        root = self.project({source_path: content})

        identity = self.application.source_manifest_identity(language, root, self.scan_policy())

        assert identity.digest_algorithm == "sha256"
        assert len(identity.digest) == 64

    def test_identity_is_immutable(self) -> None:
        root = self.project({"src/example.py": "example = 1\n"})
        identity = self.application.source_manifest_identity("python", root, self.scan_policy())

        with pytest.raises(ValidationError, match="frozen_instance"):
            identity.digest = "0" * 64

    def test_identity_rejects_an_invalid_digest(self) -> None:
        with pytest.raises(ValidationError):
            SourceManifestIdentity(digest_algorithm="sha256", digest="invalid")

    def test_identity_uses_the_exact_requested_root(self) -> None:
        first = self.project({"src/example.py": "example = 1\n"})
        second = self.project({"src/example.py": "example = 2\n"})

        first_identity = self.application.source_manifest_identity("python", first, self.scan_policy())
        second_identity = self.application.source_manifest_identity("python", second, self.scan_policy())

        assert first_identity != second_identity
