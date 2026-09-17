from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from ...resources.models.init_asset import InitAsset


@injectable
@dataclass(frozen=True)
class InitializationService:
    def target(self, project_root: Path, dot_dir: Path, asset: InitAsset) -> Path:
        root = project_root.resolve()
        bases = {"project": root, "dot_dir": self._resolve_within(root, root, dot_dir)}
        return self._resolve_within(root, bases[asset.target_base], asset.target)

    def write(self, target: Path, content: str) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def _resolve_within(self, project_root: Path, base: Path, target: Path) -> Path:
        if target.is_absolute():
            raise ValueError(f"Initialization target must be project-relative: {target}")
        resolved = (base / target).resolve()
        if not resolved.is_relative_to(project_root):
            raise ValueError(f"Initialization target escapes the project: {target}")
        return resolved
