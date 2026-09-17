import json

import pytest
from pydantic import ValidationError

from ..base_test import ArchitectureTestCase


class TestConfigurationInvariants(ArchitectureTestCase):
    def test_round_trips_json_and_yaml_without_losing_rules(self) -> None:
        config = self.application.configure(
            {
                "excluded_patterns": ["example_generated/**"],
                "boundaries": {"tags": [{"name": "example-module", "match": "src/*"}]},
                "shape": {
                    "realms": [
                        {"name": "example-source", "match": "src", "excluded_patterns": ["src/example_generated/**"]}
                    ]
                },
            }
        )
        assert self.application.configure(json.loads(config.to_json())) == config
        self.write_files({".modwire/architecture.yaml": config.to_yaml()})
        assert self.application.load_configuration(self.workspace / ".modwire") == config

    def test_configuration_is_immutable(self) -> None:
        config = self.example_configuration()
        with pytest.raises(ValidationError, match="frozen_instance"):
            config.excluded_patterns = ("example_generated/**",)
