from modwire.shared.code.models.source_class_method import SourceClassMethod
from modwire.shared.code.models.source_class_property import SourceClassProperty

from .source_symbol import SourceSymbol


class SourceClass(SourceSymbol):
    methods: list[SourceClassMethod]
    properties: list[SourceClassProperty]
