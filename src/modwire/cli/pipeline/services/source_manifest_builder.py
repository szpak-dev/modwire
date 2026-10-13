import hashlib
import json
import subprocess
from dataclasses import dataclass
from importlib import resources

from wireup import injectable

from ....extraction.extractors.models.extraction_request import ExtractionRequest
from ....shared.code.models.digest_algorithm import DigestAlgorithm
from ....shared.code.models.runtime_observation import RuntimeObservation
from ....shared.code.models.scan_policy import ScanPolicy
from ....shared.code.models.source_manifest import SourceManifest
from ..models.extractor_contract_error import ExtractorContractError
from ..models.extractor_contract_violation import ExtractorContractViolation
from ..models.extractor_execution_error import ExtractorExecutionError
from ..models.extractor_resource_error import ExtractorResourceError
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
            digest_algorithm=DigestAlgorithm.SHA256,
            digest=hashlib.sha256(serialized).hexdigest(),
        )

    def observe(self, request: ExtractionRequest) -> RuntimeObservation:
        runtime = request.runtime
        try:
            completed = subprocess.run(
                (*runtime.command, *runtime.version_arguments),
                text=True,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            diagnostic = error.stderr.strip() or error.stdout.strip()
            raise ExtractorExecutionError(runtime.descriptor.language, error.returncode, diagnostic) from error
        except OSError as error:
            raise ExtractorExecutionError(runtime.descriptor.language, -1, str(error)) from error
        version = completed.stdout.strip()
        if not version:
            raise ExtractorContractError(
                runtime.descriptor.language,
                ExtractorContractViolation.EMPTY_RUNTIME_VERSION,
                diagnostic="runtime returned an empty version",
            )
        entrypoint = runtime.entrypoint
        try:
            resource = resources.files(entrypoint.package).joinpath(entrypoint.path)
            digest = hashlib.sha256(resource.read_bytes())
        except (ImportError, OSError) as error:
            raise ExtractorResourceError(runtime.descriptor.language, entrypoint.path) from error
        return RuntimeObservation(
            version=version,
            resource_digest=digest.hexdigest(),
        )
