from dataclasses import dataclass
from fnmatch import fnmatchcase

from wireup import injectable

from ..domain import PathMatcher


@injectable(as_type=PathMatcher)
@dataclass(frozen=True)
class GlobPathMatcher(PathMatcher):
    def match(self, path: str, pattern: str, *, scope: bool) -> tuple[str, ...] | None:
        path_parts = tuple(path.replace("\\", "/").strip("/").split("/"))
        pattern_parts = tuple(pattern.replace("\\", "/").strip("/").split("/"))
        starts = (0,) if scope else range(len(path_parts))
        for start in starts:
            captures = self._match_parts(path_parts[start:], pattern_parts, ())
            if captures is not None:
                return captures
        return None

    def _match_parts(
        self, path: tuple[str, ...], pattern: tuple[str, ...], captures: tuple[str, ...]
    ) -> tuple[str, ...] | None:
        if not pattern:
            return captures
        part, *remaining = pattern
        if part == "**":
            for count in range(len(path), -1, -1):
                captured = "/".join(path[:count])
                result = self._match_parts(
                    path[count:], tuple(remaining), (*captures, captured) if captured else captures
                )
                if result is not None:
                    return result
            return None
        if not path or not path[0] or not fnmatchcase(path[0], part):
            return None
        return self._match_parts(
            path[1:], tuple(remaining), (*captures, path[0]) if any(char in part for char in "*?[") else captures
        )
