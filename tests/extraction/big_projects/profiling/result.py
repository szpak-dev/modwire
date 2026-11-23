from ..project import Project
from .document import ProfileDocument
from .resource_reason import ProfileResourceReason
from .status import ProfileStatus


class ProfileResult(ProfileDocument):
    test_id: str
    project: Project
    status: ProfileStatus
    exit_code: int
    wall_seconds: float
    limit_seconds: float
    rss_limit_bytes: int
    process_limit: int
    max_workers: int
    peak_rss_bytes: int
    peak_processes: int
    resource_samples: int
    resource_reason: ProfileResourceReason
    command: tuple[str, ...]
    profile: str = "calls.json"
    stdout: str = "stdout.log"
    stderr: str = "stderr.log"
