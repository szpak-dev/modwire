from pathlib import Path

from modwire.cli.resources.models.init_asset import InitAsset

DEFAULT_INIT_ASSETS = (
    InitAsset(source="ARCHITECTURE.md", target_base="dot_dir", target=Path("docs/ARCHITECTURE.md")),
    InitAsset(source="architecture.yaml", target_base="dot_dir", target=Path("architecture.yaml")),
    InitAsset(source="INDEX.md", target_base="dot_dir", target=Path("INDEX.md")),
    InitAsset(source="MODWIRE.md", target_base="dot_dir", target=Path("docs/MODWIRE.md")),
    InitAsset(source="RULES.md", target_base="dot_dir", target=Path("docs/RULES.md")),
    InitAsset(source="TESTING.md", target_base="dot_dir", target=Path("docs/TESTING.md")),
    InitAsset(source="WORKFLOW.md", target_base="dot_dir", target=Path("docs/WORKFLOW.md")),
    InitAsset(source="AGENTS.md", target_base="project", target=Path("AGENTS.md")),
)
