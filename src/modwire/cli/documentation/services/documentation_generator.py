from dataclasses import dataclass
from inspect import cleandoc
from pathlib import Path

from wireup import injectable

from ..models.defaults import END, START


@injectable()
@dataclass(frozen=True)
class DocumentationGenerator:
    """Render a concise README command reference from the public CLI docstring."""

    def render(self, description: str) -> str:
        return "\n".join(
            (
                START,
                "## Command reference",
                "",
                cleandoc(description),
                "",
                "| Command | Purpose |",
                "| --- | --- |",
                "| `modwire init` | Create `.modwire/` guidance and a strict architecture template. |",
                "| `modwire report --language <language>` | Analyse the configured project and render violations. |",
                "| `modwire --language <language>` | Backwards-compatible form of `report`. |",
                "",
                "Use `--summary` with `report` to render module-to-layer membership without files.",
                END,
            )
        )

    def update(self, readme: Path, check: bool, description: str) -> bool:
        """Update the README section, or report whether it is current."""
        current = readme.read_text(encoding="utf-8")
        if START not in current or END not in current:
            raise ValueError(f"Missing generated documentation markers in {readme}")
        prefix, remainder = current.split(START, 1)
        _, suffix = remainder.split(END, 1)
        expected = f"{prefix}{self.render(description)}{suffix}"
        if current == expected:
            return True
        if not check:
            readme.write_text(expected, encoding="utf-8")
        return False
