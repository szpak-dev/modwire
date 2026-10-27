import json


def example_json(example_value: str) -> str:
    return json.dumps({"example": example_value})
