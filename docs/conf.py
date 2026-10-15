from importlib import import_module

from sphinx.errors import ConfigError

project = "Modwire"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_external_toc",
]

source_suffix = {".md": "markdown"}
root_doc = "index"
external_toc_path = "_toc.yml"
external_toc_exclude_missing = True

autodoc_typehints = "description"
nitpicky = True

myst_enable_extensions = ["colon_fence", "deflist"]

exclude_patterns = ["_build"]
html_theme = "furo"
html_theme_options = {
    "source_repository": "https://github.com/szpak-dev/modwire/",
    "source_branch": "main",
    "source_directory": "docs/",
}

public_api = import_module("modwire.application")
exports = tuple(public_api.__all__)
if not exports:
    raise ConfigError("modwire.application.__all__ must publish at least one name")
if len(exports) != len(set(exports)):
    raise ConfigError("modwire.application.__all__ must contain unique names")
missing_exports = tuple(name for name in exports if not hasattr(public_api, name))
if missing_exports:
    raise ConfigError(f"modwire.application.__all__ contains unresolved names: {missing_exports!r}")
