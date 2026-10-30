import json
import re
import shutil
import subprocess
from typing import assert_never

from .language_capability_matrix.matrix import LanguageCapabilityMatrix
from .language_capability_matrix.values.enums.runtime_package_manager import RuntimePackageManager


class FixtureRuntimeContract:
    def __init__(self, matrix: LanguageCapabilityMatrix) -> None:
        self.matrix = matrix

    def document(self) -> str:
        runtimes: dict[str, object] = {}
        for language, bundle in self.matrix.languages.items():
            requirement = bundle.contract.runtime
            packages = [
                {
                    "manager": package.manager.value,
                    "name": package.name.value,
                    "version": package.version.text(),
                }
                for package in requirement.packages
            ]
            runtimes[language.value] = {
                "runtime": requirement.runtime.value,
                "executable": requirement.executable.value,
                "version": requirement.version.text(),
                "packages": packages,
            }
        return json.dumps(runtimes, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    def validate(self) -> None:
        for bundle in self.matrix.languages.values():
            requirement = bundle.contract.runtime
            executable = shutil.which(requirement.executable.value)
            if executable is None:
                raise RuntimeError(f"required runtime is unavailable: {requirement.executable.value}")
            completed = subprocess.run(
                (executable, "--version"),
                capture_output=True,
                check=True,
                text=True,
            )
            observed = re.search(r"\d+\.\d+\.\d+", f"{completed.stdout}\n{completed.stderr}")
            if observed is None:
                raise RuntimeError(f"runtime version is unreadable: {requirement.executable.value}")
            if observed.group() != requirement.version.text():
                raise RuntimeError(
                    f"{requirement.executable.value} version mismatch: "
                    f"expected {requirement.version.text()}, observed {observed.group()}"
                )
            for package in requirement.packages:
                if package.manager is RuntimePackageManager.GEM:
                    subprocess.run(
                        (
                            executable,
                            "-e",
                            'gem ARGV.fetch(0), "=" + ARGV.fetch(1)',
                            package.name.value,
                            package.version.text(),
                        ),
                        check=True,
                    )
                else:
                    assert_never(package.manager)
