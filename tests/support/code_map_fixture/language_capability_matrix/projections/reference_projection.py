from typing import Self

from pydantic import model_validator

from ...fixture_model import FixtureModel
from ..contracts.fixtures.source_set import FixtureSourceSet
from ..oracle.document import ScenarioBindingDocument
from ..values.names.language_id import LanguageId
from .mappings.identity import DeclarationIdentityKey
from .mappings.set import ProjectionMappings


class ReferenceProjection(FixtureModel):
    language: LanguageId
    fixture: FixtureSourceSet
    mappings: ProjectionMappings
    scenarios: tuple[ScenarioBindingDocument, ...]

    @property
    def canonical_parameters(self) -> set[tuple[DeclarationIdentityKey, str]]:
        callables = {item.authored: item.canonical for item in self.mappings.callables}
        return {
            (DeclarationIdentityKey(callables[item.authored_callable]), item.canonical.value)
            for item in self.mappings.parameters
        }

    @model_validator(mode="after")
    def validate_document(self) -> Self:
        self.validate_mappings()
        return self

    def validate_mappings(self) -> None:
        source_aliases = {
            item.authored.value.as_posix(): item.canonical.value.as_posix() for item in self.mappings.sources
        }
        declarations = self.mappings.declarations
        callables = self.mappings.callables
        parameters = self.mappings.parameters
        for item in (*declarations, *callables):
            if str(item.authored.source_id) not in source_aliases:
                raise ValueError("identity mapping names a source outside the reference fixture")
            if str(item.canonical.source_id) != source_aliases[str(item.authored.source_id)]:
                raise ValueError("identity mapping contradicts its source alias")
            if item.authored.family is not item.canonical.family:
                raise ValueError("identity aliases must preserve their declaration family")
        if len({DeclarationIdentityKey(item.authored) for item in declarations}) != len(declarations):
            raise ValueError("authored declaration mappings contain duplicates")
        if len({DeclarationIdentityKey(item.canonical) for item in declarations}) != len(declarations):
            raise ValueError("canonical declaration mappings contain duplicates")
        if len({DeclarationIdentityKey(item.authored) for item in callables}) != len(callables):
            raise ValueError("authored callable mappings contain duplicates")
        if len({DeclarationIdentityKey(item.canonical) for item in callables}) != len(callables):
            raise ValueError("canonical callable mappings contain duplicates")
        authored_callables = {DeclarationIdentityKey(item.authored) for item in callables}
        if any(DeclarationIdentityKey(item.authored_callable) not in authored_callables for item in parameters):
            raise ValueError("parameter mapping names an unknown authored callable")
        authored_parameters = {
            (DeclarationIdentityKey(item.authored_callable), item.authored.value) for item in parameters
        }
        if len(authored_parameters) != len(parameters):
            raise ValueError("authored parameter mappings contain duplicates")
        if len(self.canonical_parameters) != len(parameters):
            raise ValueError("canonical parameter mappings contain duplicates")
