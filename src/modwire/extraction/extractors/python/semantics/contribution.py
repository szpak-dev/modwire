from dataclasses import dataclass, field

from .....shared.code.models.callables.source_anonymous_callable import SourceAnonymousCallable
from .....shared.code.models.callables.source_call import SourceCall
from .....shared.code.models.callables.source_callable_value import SourceCallableValue
from .....shared.code.models.callables.source_class_method import SourceClassMethod
from .....shared.code.models.callables.source_function import SourceFunction
from .....shared.code.models.declarations.declaration_identity import DeclarationIdentity
from .....shared.code.models.declarations.source_declaration import SourceDeclaration
from .....shared.code.models.declarations.source_declaration_relation import SourceDeclarationRelation
from .....shared.code.models.declarations.source_namespace import SourceNamespace
from .....shared.code.models.sources.source_export import SourceExport
from .....shared.code.models.sources.source_import import SourceImport
from .....shared.code.models.values.source_class_property import SourceClassProperty
from .....shared.code.models.values.source_value import SourceValue


@dataclass(frozen=True)
class PythonSemanticContribution:
    imports: tuple[SourceImport, ...] = field(default_factory=tuple)
    exports: tuple[SourceExport, ...] = field(default_factory=tuple)
    namespaces: tuple[SourceNamespace, ...] = field(default_factory=tuple)
    declarations: tuple[SourceDeclaration, ...] = field(default_factory=tuple)
    functions: tuple[SourceFunction, ...] = field(default_factory=tuple)
    values: tuple[SourceValue, ...] = field(default_factory=tuple)
    methods: tuple[SourceClassMethod, ...] = field(default_factory=tuple)
    callable_values: tuple[SourceCallableValue, ...] = field(default_factory=tuple)
    anonymous_callables: tuple[SourceAnonymousCallable, ...] = field(default_factory=tuple)
    calls: tuple[SourceCall, ...] = field(default_factory=tuple)
    declaration_relations: tuple[SourceDeclarationRelation, ...] = field(default_factory=tuple)
    properties: dict[DeclarationIdentity, tuple[SourceClassProperty, ...]] = field(
        default_factory=dict[DeclarationIdentity, tuple[SourceClassProperty, ...]]
    )
    line_count: int = 0
    code_line_count: int = 0
    public_symbol_count: int = 0
