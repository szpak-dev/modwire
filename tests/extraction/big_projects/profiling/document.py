from typing import Literal

from pydantic import BaseModel


class ProfileDocument(BaseModel):
    schema_version: Literal[2] = 2
