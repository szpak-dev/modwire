import json
import shutil
import subprocess
from typing import assert_never

from modwire.application import ExtractorDescriptor, ModwireApplication

from .language_capability_matrix.matrix import LanguageCapabilityMatrix
from .language_capability_matrix.values.enums.runtime_package_manager import RuntimePackageManager
from .language_capability_matrix.values.names.language_id import LanguageId
from .runtime_contract_error import RuntimeContractError
from .runtime_violation import RuntimeViolation


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

    def descriptor(self, application: ModwireApplication, language: LanguageId, root: str) -> ExtractorDescriptor:
        descriptor = application.extraction.request(language.value, root).runtime.descriptor
        if descriptor.language != language.value:
            raise RuntimeContractError(
                RuntimeViolation.LANGUAGE_IDENTITY, descriptor.runtime, language.value, descriptor.language
            )
        if descriptor.runtime != self.matrix.languages[language].contract.runtime.runtime.value:
            raise RuntimeContractError(
                RuntimeViolation.RUNTIME_IDENTITY,
                descriptor.runtime,
                self.matrix.languages[language].contract.runtime.runtime.value,
                descriptor.runtime,
            )
        return descriptor

    def validate_bindings(self, application: ModwireApplication, root: str) -> None:
        for language in self.matrix.languages:
            self.descriptor(application, language, root)

    def validate(self, application: ModwireApplication, root: str) -> None:
        for language in self.matrix.languages:
            self.validate_language(application, language, root)

    def validate_language(self, application: ModwireApplication, language: LanguageId, root: str) -> None:
        self.descriptor(application, language, root)
        requirement = self.matrix.languages[language].contract.runtime
        executable = shutil.which(requirement.runtime.value)
        if executable is None:
            raise RuntimeContractError(
                RuntimeViolation.UNAVAILABLE,
                requirement.runtime.value,
                requirement.version.text(),
                "executable not found",
            )
        completed = subprocess.run(
            (executable, *requirement.probe.arguments), capture_output=True, check=False, text=True
        )
        output = f"{completed.stdout}\n{completed.stderr}".strip()
        observed = requirement.probe.pattern.search(output)
        if completed.returncode != 0 or observed is None:
            raise RuntimeContractError(
                RuntimeViolation.PROBE_FAILED, requirement.runtime.value, requirement.version.text(), output
            )
        if observed.group(1) != requirement.version.text():
            raise RuntimeContractError(
                RuntimeViolation.VERSION_MISMATCH,
                requirement.runtime.value,
                requirement.version.text(),
                observed.group(1),
            )
        for package in requirement.packages:
            if package.manager is RuntimePackageManager.GEM:
                completed = subprocess.run(
                    (
                        executable,
                        "-e",
                        'gem ARGV.fetch(0), "=" + ARGV.fetch(1)',
                        package.name.value,
                        package.version.text(),
                    ),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if completed.returncode != 0:
                    raise RuntimeContractError(
                        RuntimeViolation.PACKAGE_UNAVAILABLE,
                        requirement.runtime.value,
                        f"{package.name.value}={package.version.text()}",
                        completed.stderr.strip(),
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
