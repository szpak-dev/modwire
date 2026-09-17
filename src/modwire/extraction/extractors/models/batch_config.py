from typing import Literal

from ....shared.values.models.value_model import ValueModel


class BatchConfig(ValueModel):
    size: int = 500
    parallel_threshold: int = 0
    parallel_size: int = 0
    max_workers: int = 1
    output_format: Literal["json", "jsonl"] = "json"
