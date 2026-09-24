class BenchmarkProcessTimeout(RuntimeError):
    def __init__(self, scenario: str, phase: str, limit_seconds: float) -> None:
        self.scenario = scenario
        self.phase = phase
        self.limit_seconds = limit_seconds
        super().__init__(f"benchmark exceeded its {limit_seconds:.3f}s process budget during {scenario}.{phase}")
