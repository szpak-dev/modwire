from .declaration_identity import DeclarationIdentity
from .source_class_method import SourceClassMethod
from .source_class_property import SourceClassProperty
from .source_symbol import SourceSymbol


class SourceClass(SourceSymbol):
    declaration_id: DeclarationIdentity
    methods: list[SourceClassMethod]
    properties: list[SourceClassProperty]
