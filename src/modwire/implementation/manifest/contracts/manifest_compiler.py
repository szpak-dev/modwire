from abc import ABC, abstractmethod

from ....shared.code.models.code_map import CodeMap
from ..models.implementation_manifest import ImplementationManifest


class ManifestCompiler(ABC):
    @abstractmethod
    def compile(self, code_map: CodeMap) -> ImplementationManifest:
        raise NotImplementedError
