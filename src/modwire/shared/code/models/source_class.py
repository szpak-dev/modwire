from .source_class_method import SourceClassMethod
from .source_class_property import SourceClassProperty
from .source_symbol import SourceSymbol


class SourceClass(SourceSymbol):
    methods: list[SourceClassMethod]
    properties: list[SourceClassProperty]
