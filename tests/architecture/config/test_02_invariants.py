import pytest
from pydantic import ValidationError
from pydantic_yaml import parse_yaml_raw_as

from modwire.architecture import ArchitectureConfig
from tests.architecture.base_test import ArchitectureTestCase


class TestConfigurationInvariants(ArchitectureTestCase):
    def test_round_trips_json_and_yaml_without_losing_rules(self) -> None:
        config = ArchitectureConfig.model_validate({
            "excluded_patterns": ["example_generated/**"],
            "boundaries": {"tags": [{"name": "example-module", "match": "src/*"}]},
            "shape": {"realms": [{"name": "example-source", "match": "src",
                                  "excluded_patterns": ["src/example_generated/**"]}]},
        })
        assert ArchitectureConfig.model_validate_json(config.to_json()) == config
        assert parse_yaml_raw_as(ArchitectureConfig, config.to_yaml()) == config

    def test_configuration_is_immutable(self) -> None:
        config = self.example_configuration()
        with pytest.raises(ValidationError, match="frozen_instance"):
            config.excluded_patterns = ("example_generated/**",)
