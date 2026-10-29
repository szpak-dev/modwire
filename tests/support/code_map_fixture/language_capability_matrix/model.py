from pathlib import PurePosixPath
from typing import Self

from pydantic import Field, model_validator

from modwire.application import CodeMap, FactCapability, RelationshipFamily

from ..model import FixtureModel
from .contracts.coverage import CapabilityExpectation, LanguageContract, RelationshipExpectation
from .projections.mappings import declaration_identity_key
from .projections.model import ReferenceProjection
from .values import CapabilitySchemaVersion, LanguageId, RepositoryDocumentPath


class LanguageDocumentPair(FixtureModel):
    contract: RepositoryDocumentPath
    reference_projection: RepositoryDocumentPath


class LanguageCapabilityIndex(FixtureModel):
    schema_version: CapabilitySchemaVersion
    reference_code_map: RepositoryDocumentPath
    languages: dict[LanguageId, LanguageDocumentPair] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_document_pairs(self) -> Self:
        documents = tuple(
            path.value for pair in self.languages.values() for path in (pair.contract, pair.reference_projection)
        )
        if len(set(documents)) != len(documents):
            raise ValueError("language document paths contain duplicates")
        if any(path.is_absolute() or path.suffix != ".yaml" for path in documents):
            raise ValueError("language document paths must be relative YAML paths")
        contract_parents = {pair.contract.value.parent for pair in self.languages.values()}
        projection_parents = {pair.reference_projection.value.parent for pair in self.languages.values()}
        if len(contract_parents) != 1 or len(projection_parents) != 1:
            raise ValueError("language documents must use one contract and one projection directory")
        if contract_parents == projection_parents:
            raise ValueError("contract and projection documents must have separate directories")
        for language, pair in self.languages.items():
            expected = f"{language.value}.yaml"
            if pair.contract.value.name != expected or pair.reference_projection.value.name != expected:
                raise ValueError("language document filenames must match their language keys")
        return self


class LanguageCapabilityBundle(FixtureModel):
    contract: LanguageContract
    reference_projection: ReferenceProjection


class LanguageCapabilityMatrix(FixtureModel):
    index: LanguageCapabilityIndex
    reference_code_map: CodeMap
    languages: dict[LanguageId, LanguageCapabilityBundle]

    def capability_cases(
        self,
    ) -> tuple[tuple[LanguageId, FactCapability, CapabilityExpectation], ...]:
        return tuple(
            (language, capability, expectation)
            for language, bundle in self.languages.items()
            for capability, expectation in bundle.contract.capabilities.items()
        )

    def relationship_cases(
        self,
    ) -> tuple[tuple[LanguageId, RelationshipFamily, RelationshipExpectation], ...]:
        return tuple(
            (language, relationship, expectation)
            for language, bundle in self.languages.items()
            for relationship, expectation in bundle.contract.relationships.items()
        )

    @model_validator(mode="after")
    def validate_complete_graph(self) -> Self:
        if tuple(self.languages) != tuple(self.index.languages):
            raise ValueError("language bundles do not exactly match the root index")
        validator = LanguageCapabilityMatrixValidator(self)
        validator.validate_language_pairs()
        validator.validate_contract_coverage()
        validator.validate_projection_targets()
        return self


class LanguageCapabilityMatrixValidator:
    def __init__(self, matrix: LanguageCapabilityMatrix) -> None:
        self.matrix = matrix

    def validate_language_pairs(self) -> None:
        for language, bundle in self.matrix.languages.items():
            if bundle.contract.language != language:
                raise ValueError(f"{language.value} contract declares {bundle.contract.language.value}")
            if bundle.reference_projection.language != language:
                raise ValueError(
                    f"{language.value} reference projection declares {bundle.reference_projection.language.value}"
                )

    def validate_contract_coverage(self) -> None:
        manifest_layouts: set[tuple[tuple[str, PurePosixPath], ...]] = set()
        for bundle in self.matrix.languages.values():
            contract = bundle.contract
            if tuple(contract.capabilities) != tuple(FactCapability):
                raise ValueError(f"{contract.language.value} does not cover every fact capability")
            if tuple(contract.relationships) != tuple(RelationshipFamily):
                raise ValueError(f"{contract.language.value} does not cover every relationship family")
            contract.validate_claim_coverage()
            contract.validate_fixture_ownership()
            manifest_layouts.add(
                tuple((scenario.name.value, scenario.source.value.parent) for scenario in contract.manifests.scenarios)
            )
        if len(manifest_layouts) != 1:
            raise ValueError("language manifest contracts do not share one scenario layout")

    def validate_projection_targets(self) -> None:
        reference_sources = set(self.matrix.reference_code_map.extraction.files)
        reference_declarations = {
            declaration_identity_key(declaration.declaration_id)
            for source in self.matrix.reference_code_map.extraction.files.values()
            for declaration in source.declarations
        }
        reference_callables = {
            declaration_identity_key(callable_fact.declaration_id)
            for source in self.matrix.reference_code_map.extraction.files.values()
            for callable_fact in source.canonical_callables()
        }
        reference_parameters = {
            (declaration_identity_key(callable_fact.declaration_id), parameter.name)
            for source in self.matrix.reference_code_map.extraction.files.values()
            for callable_fact in source.canonical_callables()
            for parameter in callable_fact.parameters
        }
        for bundle in self.matrix.languages.values():
            projection = bundle.reference_projection
            projection.validate_mappings()
            suffixes = {suffix.value for suffix in bundle.contract.fixtures.source_suffixes}
            if {source.value.suffix for source in projection.fixture.sources} - suffixes:
                raise ValueError(f"{projection.language.value} reference fixture uses an undeclared suffix")
            authored_sources = {item.authored.value for item in projection.mappings.sources}
            excluded_sources = {
                source.value for source in projection.fixture.sources if source.value not in authored_sources
            }
            excluded_patterns = self.matrix.reference_code_map.extraction.manifest.policy.excluded_patterns
            if any(not any(source.match(pattern) for pattern in excluded_patterns) for source in excluded_sources):
                raise ValueError(f"{projection.language.value} projection leaves an included source unmapped")
            if {item.canonical.value.as_posix() for item in projection.mappings.sources} != reference_sources:
                raise ValueError(f"{projection.language.value} projection source targets differ from reference")
            if {
                declaration_identity_key(item.canonical) for item in projection.mappings.declarations
            } != reference_declarations:
                raise ValueError(f"{projection.language.value} declaration targets differ from reference")
            if {
                declaration_identity_key(item.canonical) for item in projection.mappings.callables
            } != reference_callables:
                raise ValueError(f"{projection.language.value} callable targets differ from reference")
            if {
                (declaration_identity_key(item.canonical_callable), item.canonical.value)
                for item in projection.mappings.parameters
            } != reference_parameters:
                raise ValueError(f"{projection.language.value} parameter targets differ from reference")
