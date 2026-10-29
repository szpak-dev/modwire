from pydantic import Field

from .....shared.code.models.callables.source_anonymous_callable import SourceAnonymousCallable
from .....shared.code.models.callables.source_callable_value import SourceCallableValue
from .....shared.code.models.callables.source_class_method import SourceClassMethod
from .....shared.code.models.callables.source_function import SourceFunction
from .....shared.code.models.declarations.source_declaration import SourceDeclaration
from .....shared.code.models.declarations.source_declaration_relation import SourceDeclarationRelation
from .....shared.code.models.declarations.source_namespace import SourceNamespace
from .....shared.code.models.source_call import SourceCall
from .....shared.code.models.sources.source_export import SourceExport
from .....shared.code.models.sources.source_import import SourceImport
from .....shared.code.models.values.source_class_property import SourceClassProperty
from .....shared.code.models.values.source_value import SourceValue
from .....shared.values.models.value_model import ValueModel


class PythonSemanticContribution(ValueModel):
    imports: tuple[SourceImport, ...] = Field(default_factory=tuple)
    exports: tuple[SourceExport, ...] = Field(default_factory=tuple)
    namespaces: tuple[SourceNamespace, ...] = Field(default_factory=tuple)
    declarations: tuple[SourceDeclaration, ...] = Field(default_factory=tuple)
    functions: tuple[SourceFunction, ...] = Field(default_factory=tuple)
    values: tuple[SourceValue, ...] = Field(default_factory=tuple)
    methods: tuple[SourceClassMethod, ...] = Field(default_factory=tuple)
    callable_values: tuple[SourceCallableValue, ...] = Field(default_factory=tuple)
    anonymous_callables: tuple[SourceAnonymousCallable, ...] = Field(default_factory=tuple)
    calls: tuple[SourceCall, ...] = Field(default_factory=tuple)
    declaration_relations: tuple[SourceDeclarationRelation, ...] = Field(default_factory=tuple)
    properties: dict[str, tuple[SourceClassProperty, ...]] = Field(default_factory=dict)
    line_count: int = 0
    code_line_count: int = 0
    public_symbol_count: int = 0
