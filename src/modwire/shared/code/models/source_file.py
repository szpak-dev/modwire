from pydantic import Field

from modwire.shared.code.models.identity import FileId, ModuleId
from modwire.shared.code.models.source_abstract_class import SourceAbstractClass
from modwire.shared.code.models.source_call import SourceCall
from modwire.shared.code.models.source_callable import SourceCallable
from modwire.shared.code.models.source_class import SourceClass
from modwire.shared.code.models.source_export import SourceExport
from modwire.shared.code.models.source_function import SourceFunction
from modwire.shared.code.models.source_import import SourceImport
from modwire.shared.code.models.source_interface import SourceInterface
from modwire.shared.code.models.source_type import SourceType
from modwire.shared.code.models.source_value import SourceValue
from modwire.shared.values.models.value_model import ValueModel


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
