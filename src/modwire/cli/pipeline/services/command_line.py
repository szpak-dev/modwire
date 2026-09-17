import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from ..models.command_request import CommandRequest


@injectable()
@dataclass(frozen=True)
class CommandLine:
    def parse(self, argv: Sequence[str]) -> CommandRequest:
        arguments = self._parser().parse_args(self._legacy_report_arguments(argv))
        return CommandRequest.model_validate(vars(arguments))

    def _parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        commands = parser.add_subparsers(dest="command", required=True)
        init = commands.add_parser("init", help="Create project-local Modwire configuration.")
        init.add_argument("--dot-dir", type=Path, default=Path(".modwire"))
        init.add_argument("--force", action="store_true", help="Replace existing generated assets.")
        report = commands.add_parser("report", help="Run architecture reports.")
        report.add_argument("--dot-dir", type=Path, default=Path(".modwire"))
        report.add_argument("--architecture-root", type=Path, default=Path("."))
        report.add_argument("--language", required=True)
        report.add_argument("--summary", action="store_true", help="Render modules without individual files.")
        return parser

    def _legacy_report_arguments(self, argv: Sequence[str]) -> Sequence[str]:
        command_names = {"init", "report", "-h", "--help"}
        return ("report", *argv) if argv and argv[0] not in command_names else argv
