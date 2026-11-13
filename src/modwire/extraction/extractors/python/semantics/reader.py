import ast
from abc import ABC, abstractmethod
from collections.abc import Hashable, Mapping
from dataclasses import dataclass

from wireup import injectable

from .....shared.code.models.callables.source_callable_kind import SourceCallableKind
from .....shared.code.models.declarations.declaration_family import DeclarationFamily
from .....shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ..observations.source_context import PythonSourceContext
from ..observations.source_observation import PythonSourceObservation
from .callables.classifier import PythonCallableClassifier
from .catalog import PythonSemanticCatalog
from .classes.classifier import PythonClassClassifier
from .contribution import PythonSemanticContribution
from .policies.declaration_identity_factory import PythonDeclarationIdentityFactory
from .policies.type_alias_classifier import PythonTypeAliasClassifier


class PythonSemanticContributor(ABC):
    @property
    @abstractmethod
    def order(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        raise NotImplementedError


class PythonSemanticReader(ABC):
    @abstractmethod
    def read(self, observation: PythonSourceObservation, context: PythonSourceContext) -> PythonSemanticCatalog:
        raise NotImplementedError


@injectable(as_type=PythonSemanticReader)
@dataclass(frozen=True)
class OrderedPythonSemanticReader(PythonSemanticReader):
    contributors: Mapping[Hashable, PythonSemanticContributor]
    classes: PythonClassClassifier
    callables: PythonCallableClassifier
    identities: PythonDeclarationIdentityFactory
    aliases: PythonTypeAliasClassifier

    def read(self, observation: PythonSourceObservation, context: PythonSourceContext) -> PythonSemanticCatalog:
        catalog = self.index(observation, context)
        for contributor in sorted(self.contributors.values(), key=lambda item: item.order):
            catalog = catalog.combine(contributor.contribute(observation, catalog, context))
        return catalog

    def index(self, observation: PythonSourceObservation, context: PythonSourceContext) -> PythonSemanticCatalog:
        identities: dict[ast.AST, DeclarationIdentity] = {}
        scopes: dict[ast.AST, ast.AST] = {}
        kinds: dict[ast.AST, SourceCallableKind] = {}
        for declaration in observation.classes:
            identities[declaration.node] = self.identities.create(
                context, self.classes.classify(declaration), declaration.qualified_name, declaration.ordinal
            )
            scopes[declaration.node] = declaration.binding_scope
        for callable in observation.callables:
            kind = self.callables.classify(callable)
            kinds[callable.node] = kind
            identities[callable.node] = self.identities.create(
                context, kind.declaration_family, callable.qualified_name, callable.ordinal
            )
            scopes[callable.node] = callable.binding_scope
        callable_values = {candidate.identity_node for candidate in observation.callables}
        property_targets = {candidate.target for candidate in observation.properties}
        for value in observation.values:
            family = DeclarationFamily.TYPE if self.aliases.is_alias(value) else DeclarationFamily.VALUE
            if family is DeclarationFamily.TYPE or (
                value.target.id != "__all__"
                and value.target not in callable_values
                and value.target not in property_targets
            ):
                identities[value.target] = self.identities.create(context, family, value.qualified_name, value.ordinal)
                scopes[value.target] = value.binding_scope
        return PythonSemanticCatalog(
            scope_identities=identities, binding_scopes=scopes, callable_kinds=kinds, inventory=observation.inventory
        )
