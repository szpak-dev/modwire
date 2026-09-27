# Modwire

## `ModwireApplication`

Public entry point for extraction, implementation manifests, architecture analysis, and the Modwire CLI.

### `create`

Create an isolated application with all services resolved through Wireup.

### `configure`

Validate architecture configuration values.

### `catalog`

Return the available architecture reports.

### `analyze`

Analyze a code map with a validated architecture configuration.

### `analyze_cached`

Analyze a code map, reusing reports for an exact map and configuration identity.

### `analyze_cached_with_diagnostics`

Analyze a code map and report the public outcome of report-cache reuse.

### `discover`

Discover supported source languages beneath a root using the caller's scan policy.

### `generate_map`

Extract one language and return its code map with honest scan metrics.

``files_excluded`` counts only source files encountered and excluded directly.
``directories_pruned`` counts directories rejected before descent; their
descendants are deliberately unobserved and are not included in file counts.

### `generate_queryable_map`

Extract source files and return a queryable code map.

### `generate_map_cached`

Return a code map with content-addressed source and complete-source-set reuse.

### `generate_map_cached_with_diagnostics`

Return a code map and public outcomes for extraction and complete-map reuse.

### `generate_queryable_map_cached`

Return a queryable code map with content-addressed persistent reuse.

### `generate_queryable_map_cached_with_diagnostics`

Return a queryable code map and public outcomes for every applicable cache stage.

### `implementation_manifest`

Publish a deterministic, provenance-bearing implementation manifest.

### `implementation_manifest_formats`

Return the implementation-manifest formats registered in this application.

### `read_implementation_manifest`

Read and canonically validate a serialized implementation manifest.

### `clear_cache`

Clear only the Modwire-owned directory for one cache namespace.

### `load_configuration`

Load and validate an architecture configuration from a directory.

### `initialize`

Create project-local Modwire configuration and agent guidance.

### `generate_documentation`

Generate this README from the published interface docstrings, or check that it is current.

### `run_extractor`

Run the native extractor transport for one supported language.

### `run`

Run the Modwire command line interface and return its process status.

## `CacheStage`

Public stages reported by cached Modwire operations.

## `CacheOutcome`

Content-safe lifecycle counts for one stage of a cached operation.

Extraction counts describe current source records. An exact code-map hit
reports its digest-backed source-set entries as extraction hits without loading
individual source payloads. Code-map and report counts describe one entry.
Invalidated entries are also misses. Diagnostics include the configured
namespace but never cache keys, source identities, or content.

## `CachedResult`

A cached operation value together with one outcome per applicable stage.

### `outcome`

Return the outcome for one applicable cache stage.

## `CacheOptions`

Generic persistent-cache settings supplied by a caller.

## `ScanPolicy`

Caller-owned filesystem traversal policy with explicit exclusions and opt-in symlink following.

## `ImplementationManifest`

A versioned, language-neutral statement of observed implementation facts and provenance.

### `validate_facts`

Validate canonical ordering, identity uniqueness, and fact references.

## `ImplementationManifestDocument`

!!! abstract "Usage Documentation"
    [Models](../concepts/models.md)

A base class for creating Pydantic models.

Attributes:
    __class_vars__: The names of the class variables defined on the model.
    __private_attributes__: Metadata about the private attributes of the model.
    __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.

    __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
    __pydantic_core_schema__: The core schema of the model.
    __pydantic_custom_init__: Whether the model has a custom `__init__` function.
    __pydantic_decorators__: Metadata containing the decorators defined on the model.
        This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
    __pydantic_generic_metadata__: A dictionary containing metadata about generic Pydantic models.
        The `origin` and `args` items map to the [`__origin__`][genericalias.__origin__]
        and [`__args__`][genericalias.__args__] attributes of [generic aliases][types-genericalias],
        and the `parameter` item maps to the `__parameter__` attribute of generic classes.
    __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
    __pydantic_post_init__: The name of the post-init method for the model, if defined.
    __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
    __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
    __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.

    __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
    __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.

    __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
        is set to `'allow'`.
    __pydantic_fields_set__: The names of fields explicitly set during instantiation.
    __pydantic_private__: Values of private attributes set on the model instance.

### `verify_digest`

Return whether the payload matches the declared digest.

### `validate_digest`

Validate that the document digest covers its exact serialized payload.

## `ManifestFormat`

!!! abstract "Usage Documentation"
    [Models](../concepts/models.md)

A base class for creating Pydantic models.

Attributes:
    __class_vars__: The names of the class variables defined on the model.
    __private_attributes__: Metadata about the private attributes of the model.
    __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.

    __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
    __pydantic_core_schema__: The core schema of the model.
    __pydantic_custom_init__: Whether the model has a custom `__init__` function.
    __pydantic_decorators__: Metadata containing the decorators defined on the model.
        This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
    __pydantic_generic_metadata__: A dictionary containing metadata about generic Pydantic models.
        The `origin` and `args` items map to the [`__origin__`][genericalias.__origin__]
        and [`__args__`][genericalias.__args__] attributes of [generic aliases][types-genericalias],
        and the `parameter` item maps to the `__parameter__` attribute of generic classes.
    __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
    __pydantic_post_init__: The name of the post-init method for the model, if defined.
    __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
    __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
    __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.

    __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
    __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.

    __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
        is set to `'allow'`.
    __pydantic_fields_set__: The names of fields explicitly set during instantiation.
    __pydantic_private__: Values of private attributes set on the model instance.

## `DeclarationFamily`

Enum where members are also (and must be) strings

## `DeclarationIdentity`

!!! abstract "Usage Documentation"
    [Models](../concepts/models.md)

A base class for creating Pydantic models.

Attributes:
    __class_vars__: The names of the class variables defined on the model.
    __private_attributes__: Metadata about the private attributes of the model.
    __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.

    __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
    __pydantic_core_schema__: The core schema of the model.
    __pydantic_custom_init__: Whether the model has a custom `__init__` function.
    __pydantic_decorators__: Metadata containing the decorators defined on the model.
        This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
    __pydantic_generic_metadata__: A dictionary containing metadata about generic Pydantic models.
        The `origin` and `args` items map to the [`__origin__`][genericalias.__origin__]
        and [`__args__`][genericalias.__args__] attributes of [generic aliases][types-genericalias],
        and the `parameter` item maps to the `__parameter__` attribute of generic classes.
    __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
    __pydantic_post_init__: The name of the post-init method for the model, if defined.
    __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
    __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
    __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.

    __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
    __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.

    __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
        is set to `'allow'`.
    __pydantic_fields_set__: The names of fields explicitly set during instantiation.
    __pydantic_private__: Values of private attributes set on the model instance.

### `canonical`

Return the stable source-qualified declaration identity.

## `DigestAlgorithm`

Digest algorithms supported by implementation-manifest artifacts.

## `FactCapability`

Versioned implementation fact families that an extractor can publish.

## `CapabilityStatus`

Declared completeness of an extractor's support for a fact family.

## `CapabilityCoverage`

An extractor's explicit support status for one implementation fact family.
