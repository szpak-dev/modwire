import sys
from collections.abc import Sequence
from pathlib import Path

from modwire.application import ModwireApplication, ScanPolicy


class CaptureCodeMapCommand:
    def __init__(self, application: ModwireApplication) -> None:
        self.application = application

    def run(self, arguments: Sequence[str]) -> None:
        if len(arguments) < 3:
            raise ValueError("expected LANGUAGE ROOT OUTPUT [EXCLUDED_PATTERN ...]")

        language, root, output = arguments[:3]
        policy = ScanPolicy(excluded_patterns=tuple(arguments[3:]), follow_symlinks=False)
        code_map = self.application.generate_map(language, root, policy)

        with Path(output).open(mode="x", encoding="utf-8") as stream:
            stream.write(code_map.to_json())
            stream.write("\n")


if __name__ == "__main__":
    CaptureCodeMapCommand(ModwireApplication.create()).run(sys.argv[1:])
