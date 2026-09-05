from modwire.shared.code.models.source_class_method import SourceClassMethod
from modwire.shared.code.models.source_class_property import SourceClassProperty
from modwire.shared.code.models.source_signature import SourceSignature

from .source_symbol import SourceSymbol


class SourceInterface(SourceSymbol):
    methods: list[SourceClassMethod]
    properties: list[SourceClassProperty]
    signatures: list[SourceSignature]
