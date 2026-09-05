from modwire.shared.code.models.source_class_method import SourceClassMethod
from modwire.shared.code.models.source_class_property import SourceClassProperty

from .source_symbol import SourceSymbol


class SourceAbstractClass(SourceSymbol):
    abstract_methods: list[SourceClassMethod]
    concrete_methods: list[SourceClassMethod]
    properties: list[SourceClassProperty]
