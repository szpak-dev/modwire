from dataclasses import dataclass

from .call_observation import PythonCallObservation
from .callable_candidate import PythonCallableCandidate
from .class_candidate import PythonClassCandidate
from .export_candidate import PythonExportCandidate
from .function_candidate import PythonFunctionCandidate
from .import_candidate import PythonImportCandidate
from .inheritance_candidate import PythonInheritanceCandidate
from .property_candidate import PythonPropertyCandidate
from .value_candidate import PythonValueCandidate


@dataclass(frozen=True)
class PythonSourceObservation:
    classes: tuple[PythonClassCandidate, ...]
    functions: tuple[PythonFunctionCandidate, ...]
    values: tuple[PythonValueCandidate, ...]
    callables: tuple[PythonCallableCandidate, ...]
    calls: tuple[PythonCallObservation, ...]
    imports: tuple[PythonImportCandidate, ...]
    exports: tuple[PythonExportCandidate, ...]
    properties: tuple[PythonPropertyCandidate, ...]
    inheritance: tuple[PythonInheritanceCandidate, ...]
