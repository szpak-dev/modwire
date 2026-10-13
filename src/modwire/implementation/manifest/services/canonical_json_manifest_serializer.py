import hashlib
import json
from dataclasses import dataclass

from pydantic import ValidationError
from wireup import injectable

from ....shared.code.models.digest_algorithm import DigestAlgorithm
from ..contracts.manifest_serializer import ManifestSerializer
from ..models.implementation_manifest import ImplementationManifest
from ..models.implementation_manifest_document import ImplementationManifestDocument
from ..models.invalid_implementation_manifest_error import InvalidImplementationManifestError
from ..models.manifest_format import ManifestFormat


@injectable(as_type=ManifestSerializer, qualifier="canonical-json")
@dataclass(frozen=True)
class CanonicalJsonManifestSerializer(ManifestSerializer):
    def format(self) -> ManifestFormat:
        return ManifestFormat(
            id="canonical-json",
            media_type="application/vnd.modwire.implementation-manifest+json",
        )

    def serialize(self, manifest: ImplementationManifest) -> ImplementationManifestDocument:
        payload = self.canonical_json(manifest)
        return ImplementationManifestDocument(
            format=self.format(),
            payload=payload,
            algorithm=DigestAlgorithm.SHA256,
            digest=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        )

    def deserialize(self, document: ImplementationManifestDocument) -> ImplementationManifest:
        if document.format != self.format():
            raise InvalidImplementationManifestError(
                document.format.id,
                "document format does not match this serializer",
            )
        try:
            manifest = ImplementationManifest.model_validate_json(document.payload)
        except ValidationError as error:
            raise InvalidImplementationManifestError(
                document.format.id,
                "document payload does not satisfy the implementation manifest schema",
            ) from error
        if self.canonical_json(manifest) != document.payload:
            raise InvalidImplementationManifestError(document.format.id, "document payload is not canonical")
        return manifest

    def canonical_json(self, manifest: ImplementationManifest) -> str:
        payload = manifest.model_dump(mode="json")
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
