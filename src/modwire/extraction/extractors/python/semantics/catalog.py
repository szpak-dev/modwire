import ast
from dataclasses import dataclass, field
from functools import singledispatchmethod

from .....shared.code.models.callables.source_anonymous_callable import SourceAnonymousCallable
from .....shared.code.models.callables.source_call import SourceCall
from .....shared.code.models.callables.source_callable import SourceCallable
from .....shared.code.models.callables.source_callable_kind import SourceCallableKind
from .....shared.code.models.callables.source_callable_value import SourceCallableValue
from .....shared.code.models.callables.source_class_method import SourceClassMethod
from .....shared.code.models.callables.source_function import SourceFunction
from .....shared.code.models.declarations.declaration_identity import DeclarationIdentity
from .....shared.code.models.declarations.source_declaration import SourceDeclaration
from .....shared.code.models.declarations.source_declaration_relation import SourceDeclarationRelation
from .....shared.code.models.declarations.source_declaration_scope import SourceDeclarationScope
from .....shared.code.models.declarations.source_file_scope import SourceFileScope
from .....shared.code.models.declarations.source_namespace import SourceNamespace
from .....shared.code.models.declarations.source_no_namespace import SourceNoNamespace
from .....shared.code.models.declarations.source_placement import SourcePlacement
from .....shared.code.models.declarations.source_resolved_target import SourceResolvedTarget
from .....shared.code.models.declarations.source_unresolved_reason import SourceUnresolvedReason
from .....shared.code.models.declarations.source_unresolved_target import SourceUnresolvedTarget
from .....shared.code.models.sources.source_export import SourceExport
from .....shared.code.models.sources.source_import import SourceImport
from .....shared.code.models.values.source_class_property import SourceClassProperty
from .....shared.code.models.values.source_value import SourceValue
from ..observations.inventory_evidence import PythonInventoryEvidence
from .contribution import PythonSemanticContribution


@dataclass(frozen=True)
class PythonSemanticCatalog:
    scope_identities: dict[ast.AST, DeclarationIdentity]
    binding_scopes: dict[ast.AST, ast.AST]
    callable_kinds: dict[ast.AST, SourceCallableKind]
    inventory: PythonInventoryEvidence
    unresolved_bindings: dict[ast.AST, dict[str, SourceUnresolvedReason]]
    wildcard_scopes: frozenset[ast.AST]
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

    def combine(self, contribution: PythonSemanticContribution) -> "PythonSemanticCatalog":
        properties = dict(self.properties)
        for name, items in contribution.properties.items():
            current = properties[name] if name in properties else ()
            properties[name] = (*current, *items)
        return PythonSemanticCatalog(
            scope_identities=self.scope_identities,
            binding_scopes=self.binding_scopes,
            callable_kinds=self.callable_kinds,
            inventory=self.inventory,
            unresolved_bindings=self.unresolved_bindings,
            wildcard_scopes=self.wildcard_scopes,
            imports=(*self.imports, *contribution.imports),
            exports=(*self.exports, *contribution.exports),
            namespaces=(*self.namespaces, *contribution.namespaces),
            declarations=(*self.declarations, *contribution.declarations),
            functions=(*self.functions, *contribution.functions),
            values=(*self.values, *contribution.values),
            methods=(*self.methods, *contribution.methods),
            callable_values=(*self.callable_values, *contribution.callable_values),
            anonymous_callables=(*self.anonymous_callables, *contribution.anonymous_callables),
            calls=(*self.calls, *contribution.calls),
            declaration_relations=(*self.declaration_relations, *contribution.declaration_relations),
            properties=properties,
            line_count=self.line_count + contribution.line_count,
            code_line_count=self.code_line_count + contribution.code_line_count,
            public_symbol_count=self.public_symbol_count + contribution.public_symbol_count,
        )

    def canonical_callables(self) -> tuple[SourceCallable, ...]:
        callables: tuple[SourceCallable, ...] = (
            *self.functions,
            *self.methods,
            *self.callable_values,
            *self.anonymous_callables,
        )
        return tuple(sorted(callables, key=lambda item: item.declaration_id.ordinal))

    def placement(self, scope: ast.AST) -> SourcePlacement:
        return SourcePlacement(lexical_scope=self.lexical_scope(scope), namespace=SourceNoNamespace())

    @singledispatchmethod
    def lexical_scope(self, scope: ast.AST) -> SourceDeclarationScope | SourceFileScope:
        return SourceDeclarationScope(declaration_id=self.scope_identities[scope])

    @lexical_scope.register
    def module_scope(self, scope: ast.Module) -> SourceDeclarationScope | SourceFileScope:
        return SourceFileScope()

    @singledispatchmethod
    def receiver_name(self, node: ast.AST) -> str:
        return ""

    @receiver_name.register(ast.FunctionDef)
    @receiver_name.register(ast.AsyncFunctionDef)
    def function_receiver(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        if self.callable_kinds[node] not in {
            SourceCallableKind.INSTANCE_METHOD,
            SourceCallableKind.CONSTRUCTOR,
            SourceCallableKind.TYPE_METHOD,
        }:
            return ""
        arguments = (*node.args.posonlyargs, *node.args.args)
        return arguments[0].arg if arguments else ""

    @singledispatchmethod
    def parameter_names(self, scope: ast.AST) -> tuple[str, ...]:
        return ()

    @parameter_names.register(ast.FunctionDef)
    @parameter_names.register(ast.AsyncFunctionDef)
    @parameter_names.register(ast.Lambda)
    def callable_parameters(self, scope: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda) -> tuple[str, ...]:
        arguments = scope.args
        names = tuple(item.arg for item in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs))
        if arguments.vararg is not None:
            names = (*names, arguments.vararg.arg)
        if arguments.kwarg is not None:
            names = (*names, arguments.kwarg.arg)
        return names

    @singledispatchmethod
    def lookup_parent(self, scope: ast.AST) -> ast.AST:
        return scope

    @lookup_parent.register
    def skip_class_lookup(self, scope: ast.ClassDef) -> ast.AST:
        return self.lookup_parent(self.binding_scopes[scope])

    def resolve(self, reference: str, binding_scope: ast.AST) -> SourceResolvedTarget | SourceUnresolvedTarget:
        parts = reference.split(".")
        scope = binding_scope
        position = 0
        while True:
            name = parts[position]
            if scope in self.unresolved_bindings and name in self.unresolved_bindings[scope]:
                return SourceUnresolvedTarget(reason=self.unresolved_bindings[scope][name])
            if scope in self.wildcard_scopes:
                return SourceUnresolvedTarget(reason=SourceUnresolvedReason.EXTERNAL)
            matches = tuple(
                node
                for node, parent in self.binding_scopes.items()
                if parent is scope
                and node in self.scope_identities
                and self.scope_identities[node].qualified_name.rsplit(".", 1)[-1] == name
            )
            if position == 0 and name == self.receiver_name(scope):
                if matches:
                    return SourceUnresolvedTarget(reason=SourceUnresolvedReason.DYNAMIC)
                scope = self.binding_scopes[scope]
                if len(parts) == 1:
                    return SourceResolvedTarget(declaration_id=self.scope_identities[scope])
                position += 1
                continue
            if name in self.parameter_names(scope):
                return SourceUnresolvedTarget(reason=SourceUnresolvedReason.DYNAMIC)
            if len(matches) > 1:
                return SourceUnresolvedTarget(reason=SourceUnresolvedReason.AMBIGUOUS)
            if matches:
                scope = matches[0]
                position += 1
                if position == len(parts):
                    return SourceResolvedTarget(declaration_id=self.scope_identities[scope])
                continue
            if position > 0:
                return SourceUnresolvedTarget(reason=SourceUnresolvedReason.UNOBSERVED)
            if scope not in self.binding_scopes:
                return SourceUnresolvedTarget(reason=SourceUnresolvedReason.EXTERNAL)
            callable_scope = scope in self.callable_kinds
            scope = self.binding_scopes[scope]
            if callable_scope:
                scope = self.lookup_parent(scope)
