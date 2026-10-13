from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from ...resources.models.init_asset import InitAsset
from ...resources.models.init_target_base import InitTargetBase
from ..models.invalid_initialization_target_error import InvalidInitializationTargetError


@injectable
@dataclass(frozen=True)
class InitializationService:
    def target(self, project_root: Path, dot_dir: Path, asset: InitAsset) -> Path:
        root = project_root.resolve()
        bases = {
            InitTargetBase.PROJECT: root,
            InitTargetBase.DOT_DIR: self._resolve_within(root, root, dot_dir),
        }
        return self._resolve_within(root, bases[asset.target_base], asset.target)

    def write(self, target: Path, content: str) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def _resolve_within(self, project_root: Path, base: Path, target: Path) -> Path:
        if target.is_absolute():
            raise InvalidInitializationTargetError(str(target), "target must be project-relative")
        resolved = (base / target).resolve()
        if not resolved.is_relative_to(project_root):
            raise InvalidInitializationTargetError(str(target), "target escapes the project")
        return resolved
