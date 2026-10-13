from .architecture_error import ArchitectureError


class UnknownFlowAnalyzerError(ArchitectureError):
    """Report a configured flow analyzer that is not registered."""

    code = "unknown_flow_analyzer"

    def __init__(self, analyzer: str, known_analyzers: tuple[str, ...]) -> None:
        self.analyzer = analyzer
        self.known_analyzers = known_analyzers
        known = ", ".join(known_analyzers) or "none"
        super().__init__(f"Unknown flow analyzer {analyzer!r}. Known analyzers: {known}")
