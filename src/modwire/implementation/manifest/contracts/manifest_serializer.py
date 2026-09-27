from abc import ABC, abstractmethod

from ..models.implementation_manifest import ImplementationManifest
from ..models.implementation_manifest_document import ImplementationManifestDocument
from ..models.manifest_format import ManifestFormat


class ManifestSerializer(ABC):
    @abstractmethod
    def format(self) -> ManifestFormat:
        raise NotImplementedError

    @abstractmethod
    def serialize(self, manifest: ImplementationManifest) -> ImplementationManifestDocument:
        raise NotImplementedError

    @abstractmethod
    def deserialize(self, document: ImplementationManifestDocument) -> ImplementationManifest:
        raise NotImplementedError
