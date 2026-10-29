from dataclasses import dataclass
from pathlib import Path

from .fixture_contract_error import FixtureContractError
from .language_capability_matrix.fixtures.inventory import FixtureSourceSet
from .language_capability_matrix.values import SourceSuffix


@dataclass(frozen=True)
class PolyglotFixtureContract:
    repository: Path

    def languages(self, root: Path) -> tuple[str, ...]:
        return tuple(sorted(path.name for path in root.iterdir() if path.is_dir()))

    def source_paths(self, root: Path) -> tuple[str, ...]:
        return tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()))

    def source_layout(self, root: Path) -> tuple[str, ...]:
        return tuple(sorted(path.parent.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()))

    def validate_language_inventory(self, root: Path, expected: tuple[str, ...]) -> None:
        actual = self.languages(root)
        if actual != expected:
            raise FixtureContractError(f"language inventory mismatch: expected {expected}, observed {actual}")

    def validate_source_inventory(self, root: Path, expected: tuple[str, ...]) -> None:
        actual = self.source_paths(root)
        if actual != expected:
            raise FixtureContractError(f"source inventory mismatch: expected {expected}, observed {actual}")

    def validate_source_set(self, fixture: FixtureSourceSet) -> None:
        self.validate_source_inventory(
            self.repository / fixture.root.value,
            tuple(source.value.as_posix() for source in fixture.sources),
        )

    def validate_source_suffixes(
        self,
        fixture: FixtureSourceSet,
        suffixes: tuple[SourceSuffix, ...],
    ) -> None:
        accepted = {suffix.value for suffix in suffixes}
        observed = {source.value.suffix for source in fixture.sources}
        unexpected = tuple(sorted(observed - accepted))
        if unexpected:
            raise FixtureContractError(f"source suffix mismatch: unexpected {unexpected}")
