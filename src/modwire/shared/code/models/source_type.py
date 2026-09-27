from .declaration_identity import DeclarationIdentity
from .source_class_property import SourceClassProperty
from .source_signature import SourceSignature
from .source_symbol import SourceSymbol


class SourceType(SourceSymbol):
    declaration_id: DeclarationIdentity
    properties: list[SourceClassProperty]
    signatures: list[SourceSignature]
