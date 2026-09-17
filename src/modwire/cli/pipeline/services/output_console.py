from rich.console import Console
from wireup import injectable


@injectable(as_type=Console)
class OutputConsole(Console):
    def __init__(self) -> None:
        super().__init__()
