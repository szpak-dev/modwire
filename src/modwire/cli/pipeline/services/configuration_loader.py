from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError
from pydantic_yaml import parse_yaml_file_as
from ruamel.yaml.error import YAMLError, YAMLStreamError
from wireup import injectable

from ....architecture.config.models.architecture_config import ArchitectureConfig
from ....architecture.config.models.architecture_config_validation_error import ArchitectureConfigValidationError
from ....architecture.config.models.architecture_config_violation import ArchitectureConfigViolation
from ..models.configuration_load_error import ConfigurationLoadError
from ..models.pipeline_violation import PipelineViolation


@injectable
@dataclass(frozen=True)
class ConfigurationLoader:
    def load(self, dot_dir: Path) -> ArchitectureConfig:
        path = dot_dir / "architecture.yaml"
        try:
            return parse_yaml_file_as(ArchitectureConfig, path)
        except OSError as error:
            raise ConfigurationLoadError(PipelineViolation.CONFIGURATION_ACCESS_FAILED, str(path)) from error
        except (YAMLError, YAMLStreamError) as error:
            raise ConfigurationLoadError(PipelineViolation.CONFIGURATION_PARSE_FAILED, str(path)) from error
        except ValidationError as error:
            raise ArchitectureConfigValidationError(
                ArchitectureConfigViolation.INVALID_CONFIGURATION,
                str(path),
            ) from error
