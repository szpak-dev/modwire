from pydantic import Field

from ....shared.code.models.source_abstract_class import SourceAbstractClass
from ....shared.code.models.source_call import SourceCall
from ....shared.code.models.source_callable import SourceCallable
from ....shared.code.models.source_class import SourceClass
from ....shared.code.models.source_export import SourceExport
from ....shared.code.models.source_function import SourceFunction
from ....shared.code.models.source_import import SourceImport
from ....shared.code.models.source_inheritance import SourceInheritance
from ....shared.code.models.source_interface import SourceInterface
from ....shared.code.models.source_type import SourceType
from ....shared.code.models.source_value import SourceValue
from ....shared.values.models.value_model import ValueModel


class ParsedSourceFile(ValueModel):
    imports: list[SourceImport] = Field(default_factory=list[SourceImport])
    exports: list[SourceExport] = Field(default_factory=list[SourceExport])
    classes: list[SourceClass] = Field(default_factory=list[SourceClass])
    interfaces: list[SourceInterface] = Field(default_factory=list[SourceInterface])
    types: list[SourceType] = Field(default_factory=list[SourceType])
    abstract_classes: list[SourceAbstractClass] = Field(default_factory=list[SourceAbstractClass])
    functions: list[SourceFunction] = Field(default_factory=list[SourceFunction])
    values: list[SourceValue] = Field(default_factory=list[SourceValue])
    callables: list[SourceCallable] = Field(default_factory=list[SourceCallable])
    calls: list[SourceCall] = Field(default_factory=list[SourceCall])
    inheritance: list[SourceInheritance] = Field(default_factory=list[SourceInheritance])
    line_count: int = 0
    code_line_count: int = 0
    public_symbol_count: int = 0
