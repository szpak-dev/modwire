from typing import Annotated

from pydantic import Field
from pydantic.dataclasses import dataclass

from ....values.models.value_model import ValueModel
from ....values.models.value_reference import ValueReference
from ..immutable_code_record import ImmutableCodeRecord
from .source_block_scope import SourceBlockScope
from .source_declaration_scope import SourceDeclarationScope
from .source_file_scope import SourceFileScope
from .source_namespace_membership import SourceNamespaceMembership
from .source_no_namespace import SourceNoNamespace


@dataclass(slots=True, kw_only=True, config=ValueModel.model_config)
class SourcePlacement(ImmutableCodeRecord):
    lexical_scope: SourceFileScope | SourceDeclarationScope | SourceBlockScope = Field(discriminator="kind")
    namespace: Annotated[
        Annotated[SourceNoNamespace | SourceNamespaceMembership, Field(discriminator="kind")], ValueReference()
    ]
