from pydantic import Field

from ..immutable_code_value import ImmutableCodeValue
from .source_block_scope import SourceBlockScope
from .source_declaration_scope import SourceDeclarationScope
from .source_file_scope import SourceFileScope
from .source_namespace_membership import SourceNamespaceMembership
from .source_no_namespace import SourceNoNamespace


class SourcePlacement(ImmutableCodeValue):
    lexical_scope: SourceFileScope | SourceDeclarationScope | SourceBlockScope = Field(discriminator="kind")
    namespace: SourceNoNamespace | SourceNamespaceMembership = Field(discriminator="kind")
