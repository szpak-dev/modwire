import os
import subprocess
from pathlib import Path

from ..support.service_test import ServiceTestCase


class ApplicationTestCase(ServiceTestCase):
    def installed_consumer(self, root: Path) -> subprocess.CompletedProcess[str]:
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
            ),
            cwd=self.workspace,
            env=environment,
            capture_output=True,
            check=False,
            text=True,
        )
