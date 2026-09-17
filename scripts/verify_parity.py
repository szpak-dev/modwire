import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

workspace = Path.cwd()
arguments = argparse.ArgumentParser(description="Compare the merged package with pinned source exports.")
arguments.add_argument("--baselines", required=True, type=Path)
original = arguments.parse_args().baselines.resolve()
baselines = workspace / ".dev/parity/baselines"
for component in ("extraction", "architecture", "cli"):
    source = original / f"modwire-{component}"
    target = baselines / f"modwire-{component}"
    if not target.exists():
        shutil.copytree(source, target)
for component, version in [("architecture", "7.0.0"), ("cli", "2.0.0")]:
    target = baselines / f"modwire-{component}/src" / f"modwire_{component}/_version.py"
    if not target.exists():
        target.write_text(f"__version__ = version = {version!r}\n")
config = {
    "boundaries": {
        "tags": [{"name": "module", "match": "src/*"}, {"name": "layer", "match": "src/*/*"}],
        "flow": {
            "module_tag": "module",
            "layers": ["layer"],
            "analyzers": ["no-cycles", "backward-flow", "no-reentry"],
        },
    },
    "shape": {"realms": [{"name": "fixture", "match": "src"}]},
}
old_script = """import json, sys
from pathlib import Path
from modwire_extraction import ModwireExtraction
from modwire_architecture import Modwire, ArchitectureConfig
app=ModwireExtraction(Path(sys.argv[1]))
code=app.generate_queryable_map(sys.argv[2])
architecture=Modwire().architecture(ArchitectureConfig.model_validate(json.loads(sys.argv[3])))
print(json.dumps({
    'code': code.code_map.model_dump(mode='json'),
    'reports': [r.model_dump(mode='json') for r in architecture.report(code)],
    'catalog': architecture.reports().model_dump(mode='json'),
}, sort_keys=True))
"""
new_script = """import json, sys
from pathlib import Path
from modwire.application import ModwireApplication
from modwire.autowiring import container
try:
    app=container.get(ModwireApplication)
    code=app.generate_queryable_map(sys.argv[2], Path(sys.argv[1]), ())
    config=app.configure(json.loads(sys.argv[3]))
    print(json.dumps({
        'code': code.code_map.model_dump(mode='json'),
        'reports': [r.model_dump(mode='json') for r in app.analyze(code, config)],
        'catalog': app.catalog().model_dump(mode='json'),
    }, sort_keys=True))
finally:
    container.close()
"""

model_mapping = json.loads((workspace / "docs/planning/report-model-migration.json").read_text())


def normalize(value):
    if isinstance(value, dict):
        return {
            k: (model_mapping.get(v, v) if k == "model" and isinstance(v, str) else normalize(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


receipt = {}
for language in ("python", "typescript", "php"):
    fixture = workspace / "tests/fixtures/languages" / language
    outputs = {}
    for label, script in [("old", old_script), ("new", new_script)]:
        env = dict(os.environ)
        env["PYTHONPATH"] = (
            os.pathsep.join(str(baselines / f"modwire-{c}/src") for c in ("extraction", "architecture"))
            if label == "old"
            else str(workspace / "src")
        )
        result = subprocess.run(
            [sys.executable, "-c", script, str(fixture), language, json.dumps(config)],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode:
            raise RuntimeError(f"{language} {label}: {result.stderr}")
        outputs[label] = json.loads(result.stdout)
        (workspace / f".dev/{language}-{label}.json").write_text(json.dumps(outputs[label], indent=2, sort_keys=True))
    normalized = normalize(outputs["old"])
    receipt[language] = {key: normalized[key] == outputs["new"][key] for key in normalized}
    print(language, receipt[language], flush=True)
    if normalized != outputs["new"]:
        (workspace / f".dev/{language}-old-normalized.json").write_text(
            json.dumps(normalized, indent=2, sort_keys=True)
        )
(workspace / ".dev/baseline-parity.json").write_text(json.dumps(receipt, indent=2))
failed = not all(all(result.values()) for result in receipt.values())

root = workspace
baseline = original / "modwire-extraction/src/modwire_extraction/extractors/languages"
paths = {str(p.relative_to(root)): str(p) for p in (root / "src/modwire").rglob("*.py") if p.name != "_version.py"}
result = subprocess.run(
    [sys.executable, str(baseline / "python/script.py"), "--batch", str(root)],
    input=json.dumps(paths),
    text=True,
    capture_output=True,
    check=True,
)
expected = json.loads(result.stdout)
result = subprocess.run(
    [sys.executable, str(workspace / "src/modwire/cli/resources/extractors/python/script.py"), "--batch", str(root)],
    input=json.dumps(paths),
    text=True,
    capture_output=True,
    check=True,
)
actual = json.loads(result.stdout)

differences = [key for key in expected if expected[key] != actual[key]]
print("Python corpus", len(paths), "files;", len(differences), "differences")
for key in differences[:10]:
    print(key, [field for field in expected[key] if expected[key][field] != actual[key][field]])
resources = []
for language in ("typescript", "php"):
    for path in (baseline / language).iterdir():
        if path.is_file() and path.suffix in {".json", ".lock", ".ts", ".js", ".mjs", ".php"}:
            target = root / "src/modwire/cli/resources/extractors" / language / path.name
            same = (
                target.exists()
                and hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(path.read_bytes()).digest()
            )
            resources.append(
                {
                    "file": str(target.relative_to(root)),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "matches": same,
                }
            )
print(
    "Native helper files:", len(resources), "compared;", sum(not item["matches"] for item in resources), "differences"
)

receipt["python_corpus"] = {"files": len(paths), "differences": differences}
receipt["native_resources"] = resources
(workspace / ".dev/baseline-parity.json").write_text(json.dumps(receipt, indent=2) + "\n")
if failed or differences or any(not item["matches"] for item in resources):
    raise SystemExit(1)
