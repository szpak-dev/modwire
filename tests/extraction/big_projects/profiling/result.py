from ..project import Project
from .document import ProfileDocument
from .status import ProfileStatus


class ProfileResult(ProfileDocument):
    test_id: str
    project: Project
    status: ProfileStatus
    exit_code: int
    wall_seconds: float
    limit_seconds: float
    command: tuple[str, ...]
    profile: str = "calls.json"
    stdout: str = "stdout.log"
    stderr: str = "stderr.log"
