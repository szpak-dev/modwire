from pydantic import Field

from ...values.models.value_model import ValueModel
from .identity import FileId, ModuleId
from .source_abstract_class import SourceAbstractClass
from .source_call import SourceCall
from .source_callable import SourceCallable
from .source_class import SourceClass
from .source_export import SourceExport
from .source_function import SourceFunction
from .source_import import SourceImport
from .source_interface import SourceInterface
from .source_type import SourceType
from .source_value import SourceValue


class SourceFile(ValueModel):
    file_id: FileId
    module_id: ModuleId
    imports: list[SourceImport]
    exports: list[SourceExport] = Field(default_factory=list[SourceExport])
    classes: list[SourceClass]
    interfaces: list[SourceInterface] = Field(default_factory=list[SourceInterface])
    types: list[SourceType] = Field(default_factory=list[SourceType])
    abstract_classes: list[SourceAbstractClass] = Field(default_factory=list[SourceAbstractClass])
    functions: list[SourceFunction]
    values: list[SourceValue] = Field(default_factory=list[SourceValue])
    callables: list[SourceCallable] = Field(default_factory=list[SourceCallable])
    calls: list[SourceCall] = Field(default_factory=list[SourceCall])
    line_count: int
    code_line_count: int
    public_symbol_count: int
