from dataclasses import dataclass, field


@dataclass
class ThreadMeasurements:
    calls: dict[tuple[str, int, str], int] = field(default_factory=dict[tuple[str, int, str], int])
