from .source_class_property import SourceClassProperty
from .source_signature import SourceSignature
from .source_symbol import SourceSymbol


class SourceType(SourceSymbol):
    properties: list[SourceClassProperty]
    signatures: list[SourceSignature]
