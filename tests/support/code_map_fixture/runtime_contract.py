import json
import shutil
import subprocess
from typing import assert_never

from modwire.application import ModwireApplication

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
                "version": requirement.version.text(),
                "packages": packages,
            }
        return json.dumps(runtimes, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    def validate_bindings(self, application: ModwireApplication, root: str) -> None:
        for language, bundle in self.matrix.languages.items():
            descriptor = application.extraction.request(language.value, root).runtime.descriptor
            if descriptor.runtime != bundle.contract.runtime.runtime.value:
                raise ValueError(f"{language.value} runtime identity differs from the registered extractor")

    def validate(self, application: ModwireApplication, root: str) -> None:
        self.validate_bindings(application, root)
        for bundle in self.matrix.languages.values():
            requirement = bundle.contract.runtime
            executable = shutil.which(requirement.runtime.value)
            if executable is None:
                raise RuntimeError(f"required runtime is unavailable: {requirement.runtime.value}")
            completed = subprocess.run(
                (executable, *requirement.probe.arguments),
                capture_output=True,
                check=True,
                text=True,
            )
            observed = requirement.probe.pattern.search(f"{completed.stdout}\n{completed.stderr}".strip())
            if observed is None:
                raise RuntimeError(f"runtime identity or version is unreadable: {requirement.runtime.value}")
            if observed.group(1) != requirement.version.text():
                raise RuntimeError(
                    f"{requirement.runtime.value} version mismatch: "
                    f"expected {requirement.version.text()}, observed {observed.group(1)}"
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

    def install_packages(self) -> None:
        for bundle in self.matrix.languages.values():
            for package in bundle.contract.runtime.packages:
                if package.manager is RuntimePackageManager.GEM:
                    subprocess.run(
                        ("gem", "install", package.name.value, "--version", package.version.text(), "--no-document"),
                        check=True,
                    )
                else:
                    assert_never(package.manager)
