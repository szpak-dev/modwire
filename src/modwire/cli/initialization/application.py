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
    """Run initialization and render a concise per-file outcome."""

    console: Console
    service: InitializationService
    resources: ResourcesApplication

    def initialize(self, project_root: Path, dot_dir: Path, force: bool) -> int:
        """Initialize the project and return a shell-compatible status code."""
        try:
            outcomes: list[tuple[str, Path]] = []
            for asset in self.resources.assets():
                target = self.service.target(project_root, dot_dir, asset)
                existed = target.exists()
                if existed and not force:
                    outcomes.append(("preserved", target))
                    continue
                self.service.write(target, self.resources.content(asset.source))
                outcomes.append(("overwritten" if existed else "created", target))
            result = InitializationResult(
                created=tuple(path for action, path in outcomes if action == "created"),
                preserved=tuple(path for action, path in outcomes if action == "preserved"),
                overwritten=tuple(path for action, path in outcomes if action == "overwritten"),
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
