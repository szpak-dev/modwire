from typing import Annotated, Literal

from pydantic.dataclasses import dataclass

from ....values.models.value_model import ValueModel
from ....values.models.value_reference import ValueReference
from ..immutable_code_record import ImmutableCodeRecord
from .declaration_identity import DeclarationIdentity
from .source_scope_kind import SourceScopeKind


@dataclass(slots=True, kw_only=True, config=ValueModel.model_config)
class SourceDeclarationScope(ImmutableCodeRecord):
    kind: Literal[SourceScopeKind.DECLARATION] = SourceScopeKind.DECLARATION
    declaration_id: Annotated[DeclarationIdentity, ValueReference()]
