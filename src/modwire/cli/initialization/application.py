from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from wireup import injectable

from ..resources.application import ResourcesApplication
from .models.initialization_result import InitializationResult
from .services.initialization_service import InitializationService


@injectable()
@dataclass(frozen=True)
class InitializationApplication:
    console: Console
    service: InitializationService
    resources: ResourcesApplication

    def initialize(self, project_root: Path, dot_dir: Path, force: bool) -> int:
        try:
            created: list[Path] = []
            preserved: list[Path] = []
            overwritten: list[Path] = []
            for asset in self.resources.assets():
                target = self.service.target(project_root, dot_dir, asset)
                existed = target.exists()
                if existed and not force:
                    preserved.append(target)
                    continue
                self.service.write(target, self.resources.content(asset.source))
                (overwritten if existed else created).append(target)
            result = InitializationResult(
                created=tuple(created),
                preserved=tuple(preserved),
                overwritten=tuple(overwritten),
            )
        except (OSError, ValueError) as error:
            self.console.print(f"Initialization failed: {error}", style="red", markup=False)
            return 1
        self._print_paths("Created", result.created, project_root)
        self._print_paths("Preserved", result.preserved, project_root)
        self._print_paths("Overwritten", result.overwritten, project_root)
        return 0

    def _print_paths(self, action: str, paths: tuple[Path, ...], project_root: Path) -> None:
        for path in paths:
            self.console.print(f"{action} {path.relative_to(project_root.resolve()).as_posix()}.")
