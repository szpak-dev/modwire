from ....fixture_model import FixtureModel
from ...values.names.executable_name import ExecutableName
from ...values.names.runtime_kind import RuntimeKind
from .package import RuntimePackageRequirement
from .version import RuntimeVersion


class RuntimeRequirement(FixtureModel):
    runtime: RuntimeKind
    executable: ExecutableName
    version: RuntimeVersion
    packages: tuple[RuntimePackageRequirement, ...]
