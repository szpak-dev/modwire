from dataclasses import dataclass
from inspect import cleandoc, getdoc
from pathlib import Path

from wireup import injectable


@injectable()
@dataclass(frozen=True)
class DocumentationGenerator:
    def render(self, public_interfaces: tuple[type[object], ...]) -> str:
        lines = ["# Modwire", ""]
        for public_interface in public_interfaces:
            documentation = getdoc(public_interface)
            if documentation is None:
                raise ValueError(f"Public interface {public_interface.__name__} requires a docstring")
            lines.extend((f"## `{public_interface.__name__}`", "", cleandoc(documentation), ""))
            for name in public_interface.__dict__:
                if name.startswith("_"):
                    continue
                callable_member = getattr(public_interface, name)
                if not callable(callable_member):
                    continue
                member_documentation = getdoc(callable_member)
                if member_documentation is None:
                    raise ValueError(f"Public interface method {public_interface.__name__}.{name} requires a docstring")
                lines.extend((f"### `{name}`", "", cleandoc(member_documentation), ""))
        return "\n".join(lines).rstrip() + "\n"

    def update(self, readme: Path, public_interfaces: tuple[type[object], ...], check: bool) -> bool:
        current = readme.read_text(encoding="utf-8") if readme.exists() else ""
        expected = self.render(public_interfaces)
        if current == expected:
            return True
        if not check:
            readme.write_text(expected, encoding="utf-8")
        return False
