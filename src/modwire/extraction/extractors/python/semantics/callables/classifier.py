import ast
from abc import ABC, abstractmethod
from collections.abc import Callable, Hashable, Mapping
from dataclasses import dataclass
from functools import cached_property, singledispatchmethod

from wireup import injectable

from ......shared.code.models.callables.source_callable_kind import SourceCallableKind
from ....models.extractor_invariant_error import ExtractorInvariantError
from ....models.extractor_invariant_violation import ExtractorInvariantViolation
from ...observations.callable_candidate import PythonCallableCandidate


class PythonCallableRule(ABC):
    @cached_property
    def is_class_scope_dispatch(self) -> Callable[[ast.AST], bool]:
        return self.is_class_scope

    @property
    @abstractmethod
    def order(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def applies(self, candidate: PythonCallableCandidate) -> bool:
        raise NotImplementedError

    @abstractmethod
    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        raise NotImplementedError

    @singledispatchmethod
    def is_class_scope(self, scope: ast.AST) -> bool:
        return False

    @is_class_scope.register
    def class_scope(self, scope: ast.ClassDef) -> bool:
        return True


class PythonCallableClassifier(ABC):
    @abstractmethod
    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        raise NotImplementedError


@injectable(as_type=PythonCallableClassifier)
@dataclass(frozen=True)
class OrderedPythonCallableClassifier(PythonCallableClassifier):
    rules: Mapping[Hashable, PythonCallableRule]

    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        for rule in sorted(self.rules.values(), key=lambda item: item.order):
            if rule.applies(candidate):
                return rule.classify(candidate)
        raise ExtractorInvariantError(ExtractorInvariantViolation.UNCLASSIFIED_CALLABLE, candidate.name)
