import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.identity import ImportSpecifier
from ......shared.code.models.source_import import SourceImport
from ......shared.code.models.source_imported_symbol import SourceImportedSymbol
from ...observations.import_candidate import PythonImportCandidate
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..policies.import_path_policy import PythonImportPathPolicy
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="60-import")
@dataclass(frozen=True)
class ImportSemanticContributor(PythonSemanticContributor):
    paths: PythonImportPathPolicy

    @property
    def order(self) -> int:
        return 60

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        return PythonSemanticContribution(
            imports=tuple(self.read(candidate, context) for candidate in observation.imports)
        )

    def read(self, candidate: PythonImportCandidate, context: PythonSourceContext) -> SourceImport:
        return self.read_node(candidate.node, candidate, context)

    @singledispatchmethod
    def read_node(
        self,
        node: ast.AST,
        candidate: PythonImportCandidate,
        context: PythonSourceContext,
    ) -> SourceImport:
        raise ValueError("Unsupported Python import candidate.")

    @read_node.register
    def read_import(
        self,
        node: ast.Import,
        candidate: PythonImportCandidate,
        context: PythonSourceContext,
    ) -> SourceImport:
        normalized_path = self.paths.normalize(candidate, context)
        return SourceImport(
            path=ImportSpecifier(candidate.path),
            is_relative=False,
            normalized_path=normalized_path,
            imported_name="",
            is_aliased=candidate.alias.asname is not None,
            crossing_type="module",
            file_barrier_crossed=True,
            statement_id=candidate.statement_id,
            join_key=str(normalized_path).rsplit("/", 1)[0],
            uses_joined_import=False,
            imported_symbols=[],
        )

    @read_node.register
    def read_import_from(
        self,
        node: ast.ImportFrom,
        candidate: PythonImportCandidate,
        context: PythonSourceContext,
    ) -> SourceImport:
        return SourceImport(
            path=ImportSpecifier(candidate.path),
            is_relative=candidate.is_relative,
            normalized_path=self.paths.normalize(candidate, context),
            imported_name=candidate.alias.name,
            is_aliased=candidate.alias.asname is not None,
            crossing_type="symbol",
            file_barrier_crossed=True,
            statement_id=candidate.statement_id,
            join_key=candidate.path,
            uses_joined_import=True,
            imported_symbols=[
                SourceImportedSymbol(
                    name=candidate.alias.name,
                    alias=candidate.alias.asname or "",
                    is_aliased=candidate.alias.asname is not None,
                    is_default=False,
                    is_namespace=False,
                    is_star=candidate.alias.name == "*",
                )
            ],
        )
