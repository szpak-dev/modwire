import argparse
import json

from modwire.application import ModwireApplication, ScanPolicy, SourceParseError


class FailureConsumer:
    def run(self) -> int:
        parser = argparse.ArgumentParser()
        parser.add_argument("root")
        parser.add_argument("--language", required=True)
        arguments = parser.parse_args()

        application = ModwireApplication.create()
        try:
            application.generate_map(arguments.language, arguments.root, ScanPolicy())
        except SourceParseError as error:
            print(
                json.dumps(
                    {
                        "column": error.column,
                        "diagnostic": error.diagnostic,
                        "language": error.language,
                        "line": error.line,
                        "path": error.path,
                        "type": type(error).__name__,
                    },
                    sort_keys=True,
                )
            )
            return 0
        raise AssertionError("Invalid source was accepted by the installed extractor.")


if __name__ == "__main__":
    raise SystemExit(FailureConsumer().run())
