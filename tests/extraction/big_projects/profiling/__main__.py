import sys
from pathlib import Path

from .profiler import CallProfiler


class ProfileWorker:
    def run(self) -> None:
        destination = Path(sys.argv[1])
        sys.argv = ["tests.extraction.big_projects.run", *sys.argv[2:]]
        CallProfiler(destination).run()


if __name__ == "__main__":
    ProfileWorker().run()
