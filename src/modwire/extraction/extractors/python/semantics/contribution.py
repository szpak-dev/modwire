from pydantic import Field

from .....shared.code.models.source_call import SourceCall
from .....shared.code.models.source_callable import SourceCallable
from .....shared.code.models.source_class_property import SourceClassProperty
from .....shared.code.models.source_declaration import SourceDeclaration
from .....shared.code.models.source_declaration_relation import SourceDeclarationRelation
from .....shared.code.models.source_export import SourceExport
from .....shared.code.models.source_function import SourceFunction
from .....shared.code.models.source_import import SourceImport
from .....shared.code.models.source_namespace import SourceNamespace
from .....shared.code.models.source_value import SourceValue
from .....shared.values.models.value_model import ValueModel


class PythonSemanticContribution(ValueModel):
    imports: tuple[SourceImport, ...] = Field(default_factory=tuple)
    exports: tuple[SourceExport, ...] = Field(default_factory=tuple)
    namespaces: tuple[SourceNamespace, ...] = Field(default_factory=tuple)
    declarations: tuple[SourceDeclaration, ...] = Field(default_factory=tuple)
    functions: tuple[SourceFunction, ...] = Field(default_factory=tuple)
    values: tuple[SourceValue, ...] = Field(default_factory=tuple)
    callables: tuple[SourceCallable, ...] = Field(default_factory=tuple)
    calls: tuple[SourceCall, ...] = Field(default_factory=tuple)
    declaration_relations: tuple[SourceDeclarationRelation, ...] = Field(default_factory=tuple)
    properties: dict[str, tuple[SourceClassProperty, ...]] = Field(default_factory=dict)
    line_count: int = 0
    code_line_count: int = 0
    public_symbol_count: int = 0
