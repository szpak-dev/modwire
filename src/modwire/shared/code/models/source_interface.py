from .source_class_method import SourceClassMethod
from .source_class_property import SourceClassProperty
from .source_signature import SourceSignature
from .source_symbol import SourceSymbol


class SourceInterface(SourceSymbol):
    methods: list[SourceClassMethod]
    properties: list[SourceClassProperty]
    signatures: list[SourceSignature]
