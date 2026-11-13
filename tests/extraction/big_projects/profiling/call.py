from pydantic import BaseModel


class ProfileCall(BaseModel):
    thread: int
    file: str
    line: int
    function: str
    calls: int
