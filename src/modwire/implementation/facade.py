from dataclasses import dataclass

from wireup import injectable

from ..shared.code.models.code_map import CodeMap
from .manifest.application import ImplementationApplication
from .manifest.models.implementation_manifest import ImplementationManifest
from .manifest.models.implementation_manifest_document import ImplementationManifestDocument
from .manifest.models.manifest_format import ManifestFormat


@injectable
@dataclass(frozen=True)
class ImplementationFacade:
    implementation: ImplementationApplication

    def formats(self) -> tuple[ManifestFormat, ...]:
        return self.implementation.formats()

    def manifest(self, code_map: CodeMap, format: ManifestFormat) -> ImplementationManifestDocument:
        return self.implementation.manifest(code_map, format)

    def read(self, document: ImplementationManifestDocument) -> ImplementationManifest:
        return self.implementation.read(document)
