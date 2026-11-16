from .call import ProfileCall
from .document import ProfileDocument


class ProfileSnapshot(ProfileDocument):
    complete: bool
    elapsed_seconds: float
    scope: str = (
        "Per-thread named Python calls in src/modwire; generated frames and native subprocess internals excluded"
    )
    calls: tuple[ProfileCall, ...]
    stack_dump: str = "stacks.log"
