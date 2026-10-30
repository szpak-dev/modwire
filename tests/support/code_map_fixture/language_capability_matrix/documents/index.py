from typing import Self

from pydantic import Field, model_validator

from ...fixture_model import FixtureModel
from ..values.names.language_id import LanguageId
from ..values.names.scenario_id import ScenarioId
from ..values.paths.document_path import RepositoryDocumentPath
from ..values.schema_version import CapabilitySchemaVersion
from .pair import LanguageDocumentPair


class LanguageCapabilityIndex(FixtureModel):
    schema_version: CapabilitySchemaVersion
    scenario_catalog: RepositoryDocumentPath
    reference_scenario: ScenarioId
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
