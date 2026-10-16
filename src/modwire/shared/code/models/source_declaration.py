from pydantic import Field

from .declaration_identity import DeclarationIdentity
from .source_class_method import SourceClassMethod
from .source_class_property import SourceClassProperty
from .source_signature import SourceSignature
from .source_symbol import SourceSymbol
from .source_symbol_kind import SourceSymbolKind


class SourceDeclaration(SourceSymbol):
    declaration_id: DeclarationIdentity
    kind: SourceSymbolKind
    methods: list[SourceClassMethod] = Field(default_factory=list[SourceClassMethod])
    abstract_methods: list[SourceClassMethod] = Field(default_factory=list[SourceClassMethod])
    properties: list[SourceClassProperty] = Field(default_factory=list[SourceClassProperty])
    signatures: list[SourceSignature] = Field(default_factory=list[SourceSignature])
