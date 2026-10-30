from typing import Self

from pydantic import model_validator

from ...fixture_model import FixtureModel
from ..contracts.fixtures.source_set import FixtureSourceSet
from ..oracle.disposition import ScenarioDisposition
from ..oracle.document import ScenarioBindingDocument
from ..values.names.language_id import LanguageId
from .mappings.identity import DeclarationIdentityKey
from .mappings.set import ProjectionMappings


class ReferenceProjection(FixtureModel):
    language: LanguageId
    fixture: FixtureSourceSet
    mappings: ProjectionMappings
    reference: ScenarioDisposition
    scenarios: tuple[ScenarioBindingDocument, ...]

    @model_validator(mode="after")
    def validate_document(self) -> Self:
        self.validate_mappings()
        return self

    def validate_mappings(self) -> None:
        authored_sources = tuple(item.authored.value.as_posix() for item in self.mappings.sources)
        canonical_sources = tuple(item.canonical.value.as_posix() for item in self.mappings.sources)
        fixture_sources = {source.value.as_posix() for source in self.fixture.sources}
        if not set(authored_sources) <= fixture_sources:
            raise ValueError("source mappings name files outside the reference fixture")
        if len(set(authored_sources)) != len(authored_sources):
            raise ValueError("authored source mappings contain duplicates")
        if len(set(canonical_sources)) != len(canonical_sources):
            raise ValueError("canonical source mappings contain duplicates")
        authored_source_ids = set(authored_sources)
        canonical_source_ids = set(canonical_sources)
        declarations = self.mappings.declarations
        callables = self.mappings.callables
        parameters = self.mappings.parameters
        if any(str(item.authored.source_id) not in authored_source_ids for item in declarations):
            raise ValueError("declaration mapping names a source outside the reference fixture")
        if any(str(item.canonical.source_id) not in canonical_source_ids for item in declarations):
            raise ValueError("declaration mapping names an unknown canonical source")
        if any(str(item.authored.source_id) not in authored_source_ids for item in callables):
            raise ValueError("callable mapping names a source outside the reference fixture")
        if any(str(item.canonical.source_id) not in canonical_source_ids for item in callables):
            raise ValueError("callable mapping names an unknown canonical source")
        if len({DeclarationIdentityKey(item.authored) for item in declarations}) != len(declarations):
            raise ValueError("authored declaration mappings contain duplicates")
        if len({DeclarationIdentityKey(item.canonical) for item in declarations}) != len(declarations):
            raise ValueError("canonical declaration mappings contain duplicates")
        if len({DeclarationIdentityKey(item.authored) for item in callables}) != len(callables):
            raise ValueError("authored callable mappings contain duplicates")
        if len({DeclarationIdentityKey(item.canonical) for item in callables}) != len(callables):
            raise ValueError("canonical callable mappings contain duplicates")
        authored_callables = {DeclarationIdentityKey(item.authored) for item in callables}
        canonical_callables = {DeclarationIdentityKey(item.canonical) for item in callables}
        if any(DeclarationIdentityKey(item.authored_callable) not in authored_callables for item in parameters):
            raise ValueError("parameter mapping names an unknown authored callable")
        if any(DeclarationIdentityKey(item.canonical_callable) not in canonical_callables for item in parameters):
            raise ValueError("parameter mapping names an unknown canonical callable")
        authored_parameters = {
            (DeclarationIdentityKey(item.authored_callable), item.authored.value) for item in parameters
        }
        canonical_parameters = {
            (DeclarationIdentityKey(item.canonical_callable), item.canonical.value) for item in parameters
        }
        if len(authored_parameters) != len(parameters):
            raise ValueError("authored parameter mappings contain duplicates")
        if len(canonical_parameters) != len(parameters):
            raise ValueError("canonical parameter mappings contain duplicates")
