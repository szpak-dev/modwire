from pathlib import Path

from pydantic import BaseModel


def parse_yaml_file_as[Model](model_type: type[Model], file: Path | str) -> Model: ...
def to_yaml_str(model: BaseModel) -> str: ...
