from pydantic import JsonValue

from ...fixture_root_model import FixtureRootModel


class YamlDocument(FixtureRootModel[JsonValue]):
    pass
