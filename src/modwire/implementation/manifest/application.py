from collections.abc import Hashable, Mapping
from dataclasses import dataclass

from wireup import injectable

from ...shared.code.models.code_map import CodeMap
from .contracts.manifest_compiler import ManifestCompiler
from .contracts.manifest_serializer import ManifestSerializer
from .models.implementation_manifest import ImplementationManifest
from .models.implementation_manifest_document import ImplementationManifestDocument
from .models.invalid_implementation_manifest_error import InvalidImplementationManifestError
from .models.manifest_format import ManifestFormat
from .models.unsupported_manifest_format_error import UnsupportedManifestFormatError


@injectable
@dataclass(frozen=True)
class ImplementationApplication:
    compiler: ManifestCompiler
    serializers: Mapping[Hashable, ManifestSerializer]

    def formats(self) -> tuple[ManifestFormat, ...]:
        formats: list[ManifestFormat] = []
        for qualifier, serializer in self.serializers.items():
            format = serializer.format()
            if qualifier != format.id:
                raise InvalidImplementationManifestError(
                    format.id,
                    f"serializer qualifier {qualifier!r} does not match its format",
                )
            formats.append(format)
        return tuple(sorted(formats, key=lambda item: item.id))

    def manifest(self, code_map: CodeMap, format: ManifestFormat) -> ImplementationManifestDocument:
        if format.id not in self.serializers:
            raise UnsupportedManifestFormatError(format, self.formats())
        serializer = self.serializers[format.id]
        if serializer.format() != format:
            raise InvalidImplementationManifestError(format.id, "registered serializer format identity differs")
        return serializer.serialize(self.compiler.compile(code_map))

    def read(self, document: ImplementationManifestDocument) -> ImplementationManifest:
        if document.format.id not in self.serializers:
            raise UnsupportedManifestFormatError(document.format, self.formats())
        serializer = self.serializers[document.format.id]
        if serializer.format() != document.format:
            raise InvalidImplementationManifestError(
                document.format.id,
                "registered serializer format identity differs",
            )
        return serializer.deserialize(document)
