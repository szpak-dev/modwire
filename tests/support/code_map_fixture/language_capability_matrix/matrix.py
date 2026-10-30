from pathlib import PurePosixPath
from typing import Self

from pydantic import model_validator

from modwire.application import CodeMap, FactCapability, RelationshipFamily

from ..fixture_model import FixtureModel
from .bundle import LanguageCapabilityBundle
from .contracts.coverage.capability import CapabilityExpectation
from .contracts.coverage.relationship import RelationshipExpectation
from .documents.index import LanguageCapabilityIndex
from .projections.mappings.identity import DeclarationIdentityKey
from .values.names.language_id import LanguageId


class LanguageCapabilityMatrix(FixtureModel):
    index: LanguageCapabilityIndex
    reference_code_map: CodeMap
    languages: dict[LanguageId, LanguageCapabilityBundle]

    def capability_cases(self) -> tuple[tuple[LanguageId, FactCapability, CapabilityExpectation], ...]:
        return tuple(
            (
                (language, capability, expectation)
                for language, bundle in self.languages.items()
                for capability, expectation in bundle.contract.capabilities.items()
            )
        )

    def relationship_cases(self) -> tuple[tuple[LanguageId, RelationshipFamily, RelationshipExpectation], ...]:
        return tuple(
            (
                (language, relationship, expectation)
                for language, bundle in self.languages.items()
                for relationship, expectation in bundle.contract.relationships.items()
            )
        )

    @model_validator(mode="after")
    def validate_complete_graph(self) -> Self:
        if tuple(self.languages) != tuple(self.index.languages):
            raise ValueError("language bundles do not exactly match the root index")
        self.validate_language_pairs()
        self.validate_manifest_layouts()
        self.validate_projection_targets()
        return self

    def validate_language_pairs(self) -> None:
        for language, bundle in self.languages.items():
            if bundle.contract.language != language:
                raise ValueError(f"{language.value} contract declares {bundle.contract.language.value}")
            if bundle.reference_projection.language != language:
                raise ValueError(
                    f"{language.value} reference projection declares {bundle.reference_projection.language.value}"
                )

    def validate_manifest_layouts(self) -> None:
        manifest_layouts: set[tuple[tuple[str, PurePosixPath], ...]] = set()
        for bundle in self.languages.values():
            contract = bundle.contract
            manifest_layouts.add(
                tuple((scenario.name.value, scenario.source.value.parent) for scenario in contract.manifests.scenarios)
            )
        if len(manifest_layouts) != 1:
            raise ValueError("language manifest contracts do not share one scenario layout")

    def validate_projection_targets(self) -> None:
        reference_sources = set(self.reference_code_map.extraction.files)
        reference_declarations = {
            DeclarationIdentityKey(declaration.declaration_id)
            for source in self.reference_code_map.extraction.files.values()
            for declaration in source.declarations
        }
        reference_callables = {
            DeclarationIdentityKey(callable_fact.declaration_id)
            for source in self.reference_code_map.extraction.files.values()
            for callable_fact in source.canonical_callables()
        }
        reference_parameters = {
            (DeclarationIdentityKey(callable_fact.declaration_id), parameter.name)
            for source in self.reference_code_map.extraction.files.values()
            for callable_fact in source.canonical_callables()
            for parameter in callable_fact.parameters
        }
        for bundle in self.languages.values():
            projection = bundle.reference_projection
            suffixes = {suffix.value for suffix in bundle.contract.fixtures.source_suffixes}
            if {source.value.suffix for source in projection.fixture.sources} - suffixes:
                raise ValueError(f"{projection.language.value} reference fixture uses an undeclared suffix")
            authored_sources = {item.authored.value for item in projection.mappings.sources}
            excluded_sources = {
                source.value for source in projection.fixture.sources if source.value not in authored_sources
            }
            excluded_patterns = self.reference_code_map.extraction.manifest.policy.excluded_patterns
            if any(not any(source.match(pattern) for pattern in excluded_patterns) for source in excluded_sources):
                raise ValueError(f"{projection.language.value} projection leaves an included source unmapped")
            if {item.canonical.value.as_posix() for item in projection.mappings.sources} != reference_sources:
                raise ValueError(f"{projection.language.value} projection source targets differ from reference")
            if {
                DeclarationIdentityKey(item.canonical) for item in projection.mappings.declarations
            } != reference_declarations:
                raise ValueError(f"{projection.language.value} declaration targets differ from reference")
            if {
                DeclarationIdentityKey(item.canonical) for item in projection.mappings.callables
            } != reference_callables:
                raise ValueError(f"{projection.language.value} callable targets differ from reference")
            if {
                (DeclarationIdentityKey(item.canonical_callable), item.canonical.value)
                for item in projection.mappings.parameters
            } != reference_parameters:
                raise ValueError(f"{projection.language.value} parameter targets differ from reference")
