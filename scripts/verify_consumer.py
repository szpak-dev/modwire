import argparse
import sys

from wireup import create_sync_container, injectable
from wireup.errors import UnknownServiceRequestedError

from modwire.application import ModwireApplication, ScanPolicy


@injectable
class CallerService:
    pass


container = create_sync_container(injectables=[sys.modules[__name__]])
try:
    assert isinstance(container.get(CallerService), CallerService)
    assert not hasattr(ModwireApplication, "__wireup_registration__")
    try:
        container.get(ModwireApplication)
    except UnknownServiceRequestedError:
        pass
    else:
        raise AssertionError("Caller discovery registered the public application")
finally:
    container.close()

parser = argparse.ArgumentParser()
parser.add_argument("root")
parser.add_argument("--language", required=True)
arguments = parser.parse_args()

application = ModwireApplication.create()
config = application.configure({"shape": {"realms": [{"name": "example-source", "match": "src"}]}})
code_map = application.generate_queryable_map(arguments.language, arguments.root, ScanPolicy())
reports = application.analyze(code_map, config)
assert code_map.files().count() == 1
assert len(reports) == 4
