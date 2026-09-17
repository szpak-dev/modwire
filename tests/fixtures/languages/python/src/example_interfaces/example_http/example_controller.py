import json as example_json

from example_application.example_actions.example_action import ExampleAction, example_command
from example_domain.example_model.example_record import ExampleRecord as ExampleRecordAlias


class ExampleController:
    def __init__(self, example_action: ExampleAction) -> None:
        self._example_action = example_action

    def example_handle(self, example_id: str) -> dict[str, str]:
        example_payload = example_json.loads('{"example_active": true}')
        example_command = example_command(ExampleRecordAlias(example_id, example_payload["example_active"]))
        return self._example_action.example_execute(example_command)
