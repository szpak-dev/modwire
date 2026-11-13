import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ....models.extractor_invariant_error import ExtractorInvariantError
from ....models.extractor_invariant_violation import ExtractorInvariantViolation
from ...observations.value_candidate import PythonValueCandidate
from .expression_reference_reader import PythonExpressionReferenceReader


class PythonTypeAliasClassifier(ABC):
    @abstractmethod
    def is_alias(self, candidate: PythonValueCandidate) -> bool:
        raise NotImplementedError


@injectable(as_type=PythonTypeAliasClassifier)
@dataclass(frozen=True)
class SyntaxTypeAliasClassifier(PythonTypeAliasClassifier):
    references: PythonExpressionReferenceReader

    def is_alias(self, candidate: PythonValueCandidate) -> bool:
        return self.statement_is_alias(candidate.statement)

    @singledispatchmethod
    def statement_is_alias(self, statement: ast.stmt) -> bool:
        raise ExtractorInvariantError(ExtractorInvariantViolation.UNSUPPORTED_VALUE_STATEMENT, type(statement).__name__)

    @statement_is_alias.register
    def assignment_is_alias(self, statement: ast.Assign) -> bool:
        return False

    @statement_is_alias.register
    def authored_alias(self, statement: ast.TypeAlias) -> bool:
        return True

    @statement_is_alias.register
    def annotated_assignment_is_alias(self, statement: ast.AnnAssign) -> bool:
        return self.references.read_expression(statement.annotation).rsplit(".", 1)[-1] == "TypeAlias"
