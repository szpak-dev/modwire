import json
import os
import subprocess
import sys
from pathlib import Path

arguments = sys.argv[1:]
if "--batch" in arguments:
    payload = sys.stdin.buffer.read()
    destination = Path(os.environ["MODWIRE_TEST_BATCHES"]) / f"{os.getpid()}.json"
    destination.write_text(json.dumps(list(json.loads(payload))), encoding="utf-8")
    result = subprocess.run(arguments, input=payload, check=False)
else:
    result = subprocess.run(arguments, check=False)
raise SystemExit(result.returncode)
