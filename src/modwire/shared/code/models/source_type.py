from modwire.shared.code.models.source_class_property import SourceClassProperty
from modwire.shared.code.models.source_signature import SourceSignature

from .source_symbol import SourceSymbol


class SourceType(SourceSymbol):
    properties: list[SourceClassProperty]
    signatures: list[SourceSignature]
