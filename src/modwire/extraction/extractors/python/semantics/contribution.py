from pydantic import Field

from .....shared.code.models.source_abstract_class import SourceAbstractClass
from .....shared.code.models.source_call import SourceCall
from .....shared.code.models.source_callable import SourceCallable
from .....shared.code.models.source_class import SourceClass
from .....shared.code.models.source_class_property import SourceClassProperty
from .....shared.code.models.source_export import SourceExport
from .....shared.code.models.source_function import SourceFunction
from .....shared.code.models.source_import import SourceImport
from .....shared.code.models.source_inheritance import SourceInheritance
from .....shared.code.models.source_interface import SourceInterface
from .....shared.code.models.source_type import SourceType
from .....shared.code.models.source_value import SourceValue
from .....shared.values.models.value_model import ValueModel


class PythonSemanticContribution(ValueModel):
    imports: tuple[SourceImport, ...] = Field(default_factory=tuple)
    exports: tuple[SourceExport, ...] = Field(default_factory=tuple)
    classes: tuple[SourceClass, ...] = Field(default_factory=tuple)
    interfaces: tuple[SourceInterface, ...] = Field(default_factory=tuple)
    types: tuple[SourceType, ...] = Field(default_factory=tuple)
    abstract_classes: tuple[SourceAbstractClass, ...] = Field(default_factory=tuple)
    functions: tuple[SourceFunction, ...] = Field(default_factory=tuple)
    values: tuple[SourceValue, ...] = Field(default_factory=tuple)
    callables: tuple[SourceCallable, ...] = Field(default_factory=tuple)
    calls: tuple[SourceCall, ...] = Field(default_factory=tuple)
    inheritance: tuple[SourceInheritance, ...] = Field(default_factory=tuple)
    properties: dict[str, tuple[SourceClassProperty, ...]] = Field(default_factory=dict)
    line_count: int = 0
    code_line_count: int = 0
    public_symbol_count: int = 0
