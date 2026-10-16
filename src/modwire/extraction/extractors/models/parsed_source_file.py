from pydantic import Field

from ....shared.code.models.source_call import SourceCall
from ....shared.code.models.source_callable import SourceCallable
from ....shared.code.models.source_declaration import SourceDeclaration
from ....shared.code.models.source_declaration_relation import SourceDeclarationRelation
from ....shared.code.models.source_export import SourceExport
from ....shared.code.models.source_function import SourceFunction
from ....shared.code.models.source_import import SourceImport
from ....shared.code.models.source_namespace import SourceNamespace
from ....shared.code.models.source_value import SourceValue
from ....shared.values.models.value_model import ValueModel


class ParsedSourceFile(ValueModel):
    imports: list[SourceImport] = Field(default_factory=list[SourceImport])
    exports: list[SourceExport] = Field(default_factory=list[SourceExport])
    namespaces: list[SourceNamespace] = Field(default_factory=list[SourceNamespace])
    declarations: list[SourceDeclaration] = Field(default_factory=list[SourceDeclaration])
    functions: list[SourceFunction] = Field(default_factory=list[SourceFunction])
    values: list[SourceValue] = Field(default_factory=list[SourceValue])
    callables: list[SourceCallable] = Field(default_factory=list[SourceCallable])
    calls: list[SourceCall] = Field(default_factory=list[SourceCall])
    declaration_relations: list[SourceDeclarationRelation] = Field(default_factory=list[SourceDeclarationRelation])
    line_count: int = 0
    code_line_count: int = 0
    public_symbol_count: int = 0
