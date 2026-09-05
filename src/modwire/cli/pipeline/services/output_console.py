from rich.console import Console
from wireup import injectable


@injectable(as_type=Console)
class OutputConsole(Console):
    """Let Wireup construct the third-party terminal service with its native defaults."""

    def __init__(self) -> None:
        super().__init__()
