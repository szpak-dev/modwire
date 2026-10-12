import pytest
from pydantic import ValidationError

from .base_test import ApplicationTestCase


class TestSourceObservation(ApplicationTestCase):
    def test_changed_cache_hit_is_rejected_after_observation(self) -> None:
        root = self.project(
            {
                "src/example_cached.py": "example_cached = 1\n",
                "src/example_changed.py": "example_changed = 1\n",
            }
        )
        policy = self.scan_policy()
        options = self.cache_options("example-observation-cache-hit-drift")
        self.application.generate_queryable_map_cached("python", root, policy, options)
        (root / "src/example_changed.py").write_text("example_changed = 2\n", encoding="utf-8")
        observation = self.application.observe_sources("python", root, policy)
        (root / "src/example_cached.py").write_text("example_cached = 2\n", encoding="utf-8")

        with pytest.raises(RuntimeError, match="Source file changed during extraction"):
            self.application.generate_queryable_map_cached_from_observation_with_diagnostics(observation, options)

    def test_added_source_is_rejected_after_observation(self) -> None:
        root = self.project({"src/example.py": "example_value = 1\n"})
        policy = self.scan_policy()
        observation = self.application.observe_sources("python", root, policy)
        (root / "src/example_added.py").write_text("example_added = 1\n", encoding="utf-8")

        with pytest.raises(RuntimeError, match="Source set changed after observation"):
            self.application.generate_queryable_map_cached_from_observation_with_diagnostics(
                observation,
                self.cache_options("example-observation-added"),
            )

    def test_removed_source_is_rejected_after_observation(self) -> None:
        root = self.project({"src/example.py": "example_value = 1\n"})
        observation = self.application.observe_sources("python", root, self.scan_policy())
        (root / "src/example.py").unlink()

        with pytest.raises(RuntimeError):
            self.application.generate_queryable_map_cached_from_observation_with_diagnostics(
                observation,
                self.cache_options("example-observation-removed"),
            )

    def test_renamed_source_is_rejected_after_observation(self) -> None:
        root = self.project({"src/example.py": "example_value = 1\n"})
        observation = self.application.observe_sources("python", root, self.scan_policy())
        (root / "src/example.py").rename(root / "src/example_renamed.py")

        with pytest.raises(RuntimeError):
            self.application.generate_queryable_map_cached_from_observation_with_diagnostics(
                observation,
                self.cache_options("example-observation-renamed"),
            )

    def test_observation_is_immutable(self) -> None:
        root = self.project({"src/example.py": "example_value = 1\n"})
        observation = self.application.observe_sources("python", root, self.scan_policy())

        with pytest.raises(ValidationError, match="frozen_instance"):
            observation.files_found = 0

    def test_change_beneath_excluded_directory_preserves_the_supplied_observation(self) -> None:
        root = self.project(
            {
                "src/example.py": "example_value = 1\n",
                "generated/example.py": "generated_value = 1\n",
            }
        )
        policy = self.configured_scan_policy(("generated/**",), False)
        observation = self.application.observe_sources("python", root, policy)
        (root / "generated/example.py").write_text("generated_value = 2\n", encoding="utf-8")

        result = self.application.generate_queryable_map_cached_from_observation_with_diagnostics(
            observation,
            self.cache_options("example-observation-excluded"),
        )

        assert result.value.source_ids() == ("src/example.py",)
        assert all(outcome.source_observation_reused for outcome in result.outcomes)

    @pytest.mark.parametrize(
        ("language", "source_path", "content"),
        (
            ("python", "src/example.py", "example_value = 1\n"),
            ("typescript", "src/example.ts", "export const exampleValue = 1;\n"),
            ("php", "src/example.php", "<?php\n$exampleValue = 1;\n"),
        ),
    )
    def test_supplied_observation_matches_identity_map_and_diagnostics(
        self,
        language: str,
        source_path: str,
        content: str,
    ) -> None:
        root = self.project({source_path: content})
        policy = self.scan_policy()
        options = self.cache_options(f"example-observation-{language}")
        observation = self.application.observe_sources(language, root, policy)

        supplied = self.application.generate_queryable_map_cached_from_observation_with_diagnostics(
            observation,
            options,
        )
        legacy = self.application.generate_queryable_map_cached_with_diagnostics(language, root, policy, options)

        assert observation.identity() == self.application.source_manifest_identity(language, root, policy)
        assert supplied.value.code_map.extraction.manifest == observation.manifest
        assert supplied.value == legacy.value
        assert all(outcome.source_observation_reused for outcome in supplied.outcomes)
        assert not any(outcome.source_observation_reused for outcome in legacy.outcomes)
