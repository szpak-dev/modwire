import runpy
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import CodeType

from .call import ProfileCall
from .snapshot import ProfileSnapshot
from .thread_measurements import ThreadMeasurements


@dataclass
class CallProfiler:
    destination: Path
    threads: dict[int, ThreadMeasurements] = field(default_factory=dict[int, ThreadMeasurements])
    stopped: threading.Event = field(default_factory=threading.Event)
    started: float = field(default_factory=time.perf_counter)

    def observe(self, code: CodeType, instruction_offset: int) -> object:
        filename = code.co_filename
        if "/src/modwire/" not in filename or code.co_name.startswith("<"):
            return sys.monitoring.DISABLE
        thread_id = threading.get_ident()
        if thread_id not in self.threads:
            self.threads[thread_id] = ThreadMeasurements()
        calls = self.threads[thread_id].calls
        key = (filename.partition("/src/")[2], code.co_firstlineno, code.co_name)
        if key not in calls:
            calls[key] = 0
        calls[key] += 1
        return None

    def write(self, complete: bool) -> None:
        snapshot = ProfileSnapshot(
            complete=complete,
            elapsed_seconds=time.perf_counter() - self.started,
            calls=tuple(
                ProfileCall(
                    thread=thread_id,
                    file=file,
                    line=line,
                    function=function,
                    calls=count,
                )
                for thread_id, thread in self.threads.copy().items()
                for (file, line, function), count in thread.calls.copy().items()
            ),
        )
        temporary = self.destination.with_suffix(".tmp")
        temporary.write_text(snapshot.model_dump_json(indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.destination)

    def checkpoint(self) -> None:
        while not self.stopped.wait(0.25):
            self.write(False)

    def run(self) -> None:
        self.write(False)
        writer = threading.Thread(target=self.checkpoint, name="profile-checkpoint")
        writer.start()
        sys.monitoring.use_tool_id(sys.monitoring.PROFILER_ID, "modwire-call-profile")
        sys.monitoring.register_callback(sys.monitoring.PROFILER_ID, sys.monitoring.events.PY_START, self.observe)
        sys.monitoring.set_events(sys.monitoring.PROFILER_ID, sys.monitoring.events.PY_START)
        try:
            runpy.run_module("tests.extraction.big_projects.run", run_name="__main__")
        finally:
            sys.monitoring.set_events(sys.monitoring.PROFILER_ID, sys.monitoring.events.NO_EVENTS)
            sys.monitoring.register_callback(sys.monitoring.PROFILER_ID, sys.monitoring.events.PY_START, None)
            sys.monitoring.free_tool_id(sys.monitoring.PROFILER_ID)
            self.stopped.set()
            writer.join()
            self.write(True)
