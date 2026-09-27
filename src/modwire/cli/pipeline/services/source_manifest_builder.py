import hashlib
import json
import subprocess
from dataclasses import dataclass
from importlib import resources

from wireup import injectable

from ....extraction.extractors.models.extraction_request import ExtractionRequest
from ....shared.code.models.runtime_observation import RuntimeObservation
from ....shared.code.models.scan_policy import ScanPolicy
from ....shared.code.models.source_manifest import SourceManifest
from ..models.source_entry import SourceEntry


@injectable
@dataclass(frozen=True)
class SourceManifestBuilder:
    def build(
        self,
        policy: ScanPolicy,
        runtime: RuntimeObservation,
        entries: tuple[SourceEntry, ...],
    ) -> SourceManifest:
        sources = tuple(
            entry.artifact() for entry in sorted(entries, key=lambda item: (str(item.source_id), item.relative_path))
        )
        payload = {
            "policy": policy.model_dump(mode="json"),
            "runtime": runtime.model_dump(mode="json"),
            "sources": [source.model_dump(mode="json") for source in sources],
        }
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return SourceManifest(
            policy=policy,
            runtime=runtime,
            sources=sources,
            digest_algorithm="sha256",
            digest=hashlib.sha256(serialized).hexdigest(),
        )

    def observe(self, request: ExtractionRequest) -> RuntimeObservation:
        runtime = request.runtime
        completed = subprocess.run(
            (*runtime.command, *runtime.version_arguments),
            text=True,
            capture_output=True,
            check=True,
        )
        version = completed.stdout.strip()
        if not version:
            raise RuntimeError(f"{runtime.descriptor.language} runtime returned an empty version.")
        digest = hashlib.sha256()
        for resource in runtime.resources.identity_resources:
            digest.update(resource.package.encode("utf-8"))
            digest.update(b"\x00")
            digest.update(resource.path.encode("utf-8"))
            digest.update(b"\x00")
            digest.update(resources.files(resource.package).joinpath(resource.path).read_bytes())
            digest.update(b"\x00")
        return RuntimeObservation(
            version=version,
            resource_digest=digest.hexdigest(),
        )
