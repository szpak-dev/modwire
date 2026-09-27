from dataclasses import dataclass
from importlib import metadata

from wireup import injectable

from ..domain import PackageVersion


@injectable(as_type=PackageVersion)
@dataclass(frozen=True)
class InstalledPackageVersion(PackageVersion):
    def version(self) -> str:
        return metadata.version("modwire")
