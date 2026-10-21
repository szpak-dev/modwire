import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

from modwire.application import CacheOptions

from ..support.service_test import ServiceTestCase


class ApplicationTestCase(ServiceTestCase):
    def cache_options(self, namespace: str) -> CacheOptions:
        return CacheOptions(directory=str(self.workspace / "cache"), namespace=namespace, max_bytes=10_000_000)

    def installed_consumer(self, root: Path, language: str) -> subprocess.CompletedProcess[str]:
        distribution = self.workspace / "distribution"
        subprocess.run(
            ("uv", "build", "--wheel", "--out-dir", str(distribution)),
            cwd=self.repository,
            capture_output=True,
            check=True,
            text=True,
        )
        wheel = next(distribution.glob("modwire-*.whl"))
        environment = dict(os.environ)
        environment["UV_CACHE_DIR"] = str(self.repository / ".dev/cache/uv")
        return subprocess.run(
            (
                "uv",
                "run",
                "--isolated",
                "--no-project",
                "--with",
                str(wheel),
                "python",
                str(self.repository / "scripts/verify_consumer.py"),
                str(root),
                "--language",
                language,
            ),
            cwd=self.workspace,
            env=environment,
            capture_output=True,
            check=False,
            text=True,
        )

    def installed_failure_consumer(self, root: Path, language: str) -> subprocess.CompletedProcess[str]:
        distribution = self.workspace / "failure-distribution"
        subprocess.run(
            ("uv", "build", "--wheel", "--out-dir", str(distribution)),
            cwd=self.repository,
            capture_output=True,
            check=True,
            text=True,
        )
        wheel = next(distribution.glob("modwire-*.whl"))
        environment = dict(os.environ)
        environment["UV_CACHE_DIR"] = str(self.repository / ".dev/cache/uv")
        return subprocess.run(
            (
                "uv",
                "run",
                "--isolated",
                "--no-project",
                "--with",
                str(wheel),
                "python",
                str(self.repository / "scripts/verify_failure_consumer.py"),
                str(root),
                "--language",
                language,
            ),
            cwd=self.workspace,
            env=environment,
            capture_output=True,
            check=False,
            text=True,
        )

    def failure_consumer(
        self,
        root: Path,
        language: str,
        environment: Mapping[str, str],
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            (
                sys.executable,
                str(self.repository / "tests/application/failure_consumer.py"),
                str(root),
                language,
            ),
            cwd=self.workspace,
            env=environment,
            capture_output=True,
            check=False,
            text=True,
        )
