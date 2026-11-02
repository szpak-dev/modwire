from ....fixture_model import FixtureModel
from ...values.enums.runtime_package_manager import RuntimePackageManager
from ...values.names.package_name import PackageName
from .version import RuntimeVersion


class RuntimePackageRequirement(FixtureModel):
    manager: RuntimePackageManager
    name: PackageName
    version: RuntimeVersion
