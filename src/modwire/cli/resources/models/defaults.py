from pathlib import Path

from .init_asset import InitAsset
from .init_target_base import InitTargetBase

DEFAULT_INIT_ASSETS = (
    InitAsset(source="ARCHITECTURE.md", target_base=InitTargetBase.DOT_DIR, target=Path("docs/ARCHITECTURE.md")),
    InitAsset(source="architecture.yaml", target_base=InitTargetBase.DOT_DIR, target=Path("architecture.yaml")),
    InitAsset(source="INDEX.md", target_base=InitTargetBase.DOT_DIR, target=Path("INDEX.md")),
    InitAsset(source="MODWIRE.md", target_base=InitTargetBase.DOT_DIR, target=Path("docs/MODWIRE.md")),
    InitAsset(source="RULES.md", target_base=InitTargetBase.DOT_DIR, target=Path("docs/RULES.md")),
    InitAsset(source="TESTING.md", target_base=InitTargetBase.DOT_DIR, target=Path("docs/TESTING.md")),
    InitAsset(source="WORKFLOW.md", target_base=InitTargetBase.DOT_DIR, target=Path("docs/WORKFLOW.md")),
    InitAsset(source="AGENTS.md", target_base=InitTargetBase.PROJECT, target=Path("AGENTS.md")),
)
