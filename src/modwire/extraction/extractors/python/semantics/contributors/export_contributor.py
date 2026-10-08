import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.identity import ImportSpecifier
from ......shared.code.models.types import SourceExportKind
from ...observations.export_candidate import PythonExportCandidate
from ...observations.import_candidate import PythonImportCandidate
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ...observations.value_candidate import PythonValueCandidate
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..exports.classifier import PythonExportClassifier
from ..policies.import_path_policy import PythonImportPathPolicy
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="70-export")
@dataclass(frozen=True)
class ExportSemanticContributor(PythonSemanticContributor):
    exports: PythonExportClassifier
    paths: PythonImportPathPolicy

    @property
    def order(self) -> int:
        return 70

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        declarations = self.declaration_candidates(catalog)
        imported = self.import_candidates(observation.imports, context)
        explicit, names = self.explicit_names(observation.values)
        candidates: tuple[PythonExportCandidate, ...]
        if explicit:
            candidates = tuple(self.explicit_candidate(name, declarations, imported) for name in sorted(names))
        else:
            candidates = tuple(item for name, item in declarations.items() if not name.startswith("_"))
        return PythonSemanticContribution(
            exports=tuple(
                source_export for candidate in candidates for source_export in self.exports.classify(candidate)
            )
        )

    def declaration_candidates(self, catalog: PythonSemanticCatalog) -> dict[str, PythonExportCandidate]:
        candidates: dict[str, PythonExportCandidate] = {}
        for item in catalog.classes:
            candidates[item.name] = self.direct_candidate(item.name, "class", False)
        for item in catalog.abstract_classes:
            candidates[item.name] = self.direct_candidate(item.name, "abstract_class", False)
        for item in catalog.functions:
            candidates[item.name] = self.direct_candidate(item.name, "function", False)
        return candidates

    def import_candidates(
        self,
        imports: tuple[PythonImportCandidate, ...],
        context: PythonSourceContext,
    ) -> dict[str, PythonExportCandidate]:
        candidates: dict[str, PythonExportCandidate] = {}
        for candidate in imports:
            item = self.import_candidate(candidate, context)
            if item.name:
                candidates[item.name] = item
        return candidates

    def import_candidate(
        self,
        candidate: PythonImportCandidate,
        context: PythonSourceContext,
    ) -> PythonExportCandidate:
        return self.import_from_node(candidate.node, candidate, context)

    @singledispatchmethod
    def import_from_node(
        self,
        node: ast.AST,
        candidate: PythonImportCandidate,
        context: PythonSourceContext,
    ) -> PythonExportCandidate:
        return self.direct_candidate("", "unknown", False)

    @import_from_node.register
    def import_from_node_candidate(
        self,
        node: ast.ImportFrom,
        candidate: PythonImportCandidate,
        context: PythonSourceContext,
    ) -> PythonExportCandidate:
        return PythonExportCandidate(
            name=candidate.alias.asname or candidate.alias.name,
            local_name=candidate.alias.name,
            kind="unknown",
            path=ImportSpecifier(candidate.path),
            is_relative=candidate.is_relative,
            normalized_path=self.paths.normalize(candidate, context),
            is_reexport=True,
            is_aliased=candidate.alias.asname is not None,
            statement_id=candidate.statement_id,
            explicit=True,
        )

    def explicit_names(self, values: tuple[PythonValueCandidate, ...]) -> tuple[bool, tuple[str, ...]]:
        found = False
        names: tuple[str, ...] = ()
        for candidate in values:
            if candidate.target.id != "__all__":
                continue
            relevant, valid, incoming_names = self.statement_names(candidate.statement)
            if not relevant:
                continue
            found = True
            if not valid:
                return (False, ())
            names = incoming_names
        return (found, names)

    @singledispatchmethod
    def statement_names(self, statement: ast.stmt) -> tuple[bool, bool, tuple[str, ...]]:
        return (True, False, ())

    @statement_names.register
    def assignment_names(self, statement: ast.Assign) -> tuple[bool, bool, tuple[str, ...]]:
        valid, names = self.expression_names(statement.value)
        return (True, valid, names)

    @statement_names.register
    def annotated_assignment_names(self, statement: ast.AnnAssign) -> tuple[bool, bool, tuple[str, ...]]:
        if statement.value is None:
            return (False, False, ())
        valid, names = self.expression_names(statement.value)
        return (True, valid, names)

    @singledispatchmethod
    def expression_names(self, expression: ast.expr) -> tuple[bool, tuple[str, ...]]:
        return (False, ())

    @expression_names.register
    def list_names(self, expression: ast.List) -> tuple[bool, tuple[str, ...]]:
        return self.element_names(expression.elts)

    @expression_names.register
    def tuple_names(self, expression: ast.Tuple) -> tuple[bool, tuple[str, ...]]:
        return self.element_names(expression.elts)

    def element_names(self, elements: list[ast.expr]) -> tuple[bool, tuple[str, ...]]:
        names: list[str] = []
        for element in elements:
            valid, name = self.string_value(element)
            if not valid:
                return (False, ())
            names.append(name)
        return (True, tuple(set(names)))

    @singledispatchmethod
    def string_value(self, expression: ast.expr) -> tuple[bool, str]:
        return (False, "")

    @string_value.register
    def constant_string_value(self, expression: ast.Constant) -> tuple[bool, str]:
        return self.literal_string(expression.value)

    @singledispatchmethod
    def literal_string(
        self,
        value: str | bytes | int | float | complex | bool,
    ) -> tuple[bool, str]:
        return (False, "")

    @literal_string.register
    def string_literal(self, value: str) -> tuple[bool, str]:
        return (True, value)

    def explicit_candidate(
        self,
        name: str,
        declarations: dict[str, PythonExportCandidate],
        imported: dict[str, PythonExportCandidate],
    ) -> PythonExportCandidate:
        if name in imported:
            return imported[name]
        if name in declarations:
            item = declarations[name]
            return PythonExportCandidate(
                name=item.name,
                local_name=item.local_name,
                kind=item.kind,
                path=item.path,
                is_relative=item.is_relative,
                normalized_path=item.normalized_path,
                is_reexport=item.is_reexport,
                is_aliased=item.is_aliased,
                statement_id=item.statement_id,
                explicit=True,
            )
        return self.direct_candidate(name, "unknown", True)

    def direct_candidate(
        self,
        name: str,
        kind: SourceExportKind,
        explicit: bool,
    ) -> PythonExportCandidate:
        return PythonExportCandidate(
            name=name,
            local_name=name,
            kind=kind,
            path=ImportSpecifier(""),
            is_relative=False,
            normalized_path=ImportSpecifier(""),
            is_reexport=False,
            is_aliased=False,
            statement_id=0,
            explicit=explicit,
        )
