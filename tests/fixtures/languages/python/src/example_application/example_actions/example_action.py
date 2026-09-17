from dataclasses import dataclass

from example_domain.example_model.example_record import ExampleRecord
from example_domain.example_services.example_policy import ExamplePolicy, example_allowed


@dataclass(frozen=True)
class ExampleAction:
    example_actor: str = "example_system"

    def example_execute(self, example_record: ExampleRecord) -> dict[str, str]:
        if not ExamplePolicy().example_allows(example_record):
            return {"example_status": "example_blocked"}
        return {"example_status": "example_complete", "example_id": example_record.example_id}


def example_command(example_record: ExampleRecord) -> ExampleRecord:
    return example_record


def example_label(example_record: ExampleRecord) -> str:
    return "example_allowed" if example_allowed(example_record) else "example_blocked"


def example_nullable(example_value: str | None) -> str:
    return example_value or "example_missing"
