#!/usr/bin/env php
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use PhpParser\Error;
use PhpParser\Node;
use PhpParser\Node\Arg;
use PhpParser\Node\Expr;
use PhpParser\Node\Name;
use PhpParser\Node\Param;
use PhpParser\Node\Stmt;
use PhpParser\ParserFactory;
use PhpParser\PrettyPrinter\Standard;

function line_count_for_content(string $content): int {
    return max(1, substr_count($content, "\n") + 1);
}

function code_line_count_for_content(string $content): int {
    $count = 0;
    foreach (explode("\n", $content) as $line) {
        $trimmed = trim($line);
        if (
            $trimmed !== ''
            && !str_starts_with($trimmed, '//')
            && !str_starts_with($trimmed, '#')
            && !str_starts_with($trimmed, '/*')
            && !str_starts_with($trimmed, '*')
        ) {
            $count++;
        }
    }
    return $count;
}

function source_id_for_path(string $path, string $sourcesRoot): string {
    $normalizedPath = str_replace('\\', '/', realpath($path) ?: $path);
    $normalizedRoot = rtrim(str_replace('\\', '/', realpath($sourcesRoot) ?: $sourcesRoot), '/');
    if ($normalizedRoot !== '' && str_starts_with($normalizedPath, $normalizedRoot . '/')) {
        $normalizedPath = substr($normalizedPath, strlen($normalizedRoot) + 1);
    }
    return trim(preg_replace('/\.php$/', '', $normalizedPath), '/');
}

function line_span(Node $node): int {
    return max(1, $node->getEndLine() - $node->getStartLine() + 1);
}

function declaration_ordinal(Node $node): int {
    return $node->getStartFilePos() + 1;
}

function visibility_intent(string $name, string $visibility): string {
    $magicMethods = [
        '__call', '__callStatic', '__clone', '__construct', '__debugInfo', '__destruct',
        '__get', '__invoke', '__isset', '__serialize', '__set', '__set_state', '__sleep',
        '__toString', '__unserialize', '__unset', '__wakeup',
    ];
    if (in_array($name, $magicMethods, true)) {
        return $visibility;
    }
    if (str_starts_with($name, '__')) {
        return 'private';
    }
    if (str_starts_with($name, '_')) {
        return 'protected';
    }
    return $visibility;
}

function node_name(Node|Name|string|null $node): string {
    if ($node instanceof Name) {
        return $node->toString();
    }
    if ($node instanceof Node\Identifier || $node instanceof Node\VarLikeIdentifier) {
        return $node->toString();
    }
    if (is_string($node)) {
        return $node;
    }
    return '';
}

function var_name(Expr $expr): string {
    return $expr instanceof Expr\Variable && is_string($expr->name) ? $expr->name : '';
}

function normalize_import_path(string $value): string {
    return trim(str_replace('\\', '/', $value), '/ ');
}

function import_parent_path(string $value): string {
    $parts = explode('/', normalize_import_path($value));
    array_pop($parts);
    return implode('/', $parts);
}

function imported_symbol_name(string $path): string {
    $parts = explode('/', normalize_import_path($path));
    return end($parts) ?: '';
}

function walk_nodes(array $nodes, callable $callback, array $parents = []): void {
    foreach ($nodes as $node) {
        if (!$node instanceof Node) {
            continue;
        }
        $callback($node, $parents);
        $nextParents = [...$parents, $node];
        foreach ($node->getSubNodeNames() as $name) {
            $child = $node->{$name};
            if ($child instanceof Node) {
                walk_nodes([$child], $callback, $nextParents);
            } elseif (is_array($child)) {
                walk_nodes($child, $callback, $nextParents);
            }
        }
    }
}

function nearest_parent(array $parents, string ...$classes): ?Node {
    for ($index = count($parents) - 1; $index >= 0; $index--) {
        foreach ($classes as $class) {
            if ($parents[$index] instanceof $class) {
                return $parents[$index];
            }
        }
    }
    return null;
}

function is_top_level(array $parents): bool {
    foreach ($parents as $parent) {
        if (!$parent instanceof Stmt\Namespace_) {
            return false;
        }
    }
    return true;
}

function function_parent(array $parents): ?Node {
    return nearest_parent(
        $parents,
        Stmt\ClassMethod::class,
        Stmt\Function_::class,
        Expr\Closure::class,
        Expr\ArrowFunction::class,
    );
}

function class_visibility(Stmt\ClassLike $node): string {
    return 'public';
}

function member_visibility(Stmt\ClassMethod|Stmt\Property|Stmt\ClassConst $node): string {
    if ($node->isPrivate()) {
        return 'private';
    }
    if ($node->isProtected()) {
        return 'protected';
    }
    return 'public';
}

function parameter_visibility(Param $param): string {
    if (($param->flags & Stmt\Class_::MODIFIER_PRIVATE) !== 0) {
        return 'private';
    }
    if (($param->flags & Stmt\Class_::MODIFIER_PROTECTED) !== 0) {
        return 'protected';
    }
    return 'public';
}

function type_annotation(Node|Name|string|null $type): string {
    if ($type instanceof Node\NullableType) {
        return '?' . type_annotation($type->type);
    }
    if ($type instanceof Node\UnionType) {
        return implode('|', array_map(
            fn (Node $item): string => $item instanceof Node\IntersectionType
                ? '(' . type_annotation($item) . ')'
                : type_annotation($item),
            $type->types
        ));
    }
    if ($type instanceof Node\IntersectionType) {
        return implode('&', array_map(type_annotation(...), $type->types));
    }
    if ($type instanceof Name) {
        return $type->toCodeString();
    }
    return node_name($type);
}

function source_type(Node|Name|string|null $type): array {
    if ($type === null || $type === '') {
        return ['kind' => 'absent'];
    }
    if ($type instanceof Name || $type instanceof Node\Identifier || is_string($type)) {
        return [
            'kind' => 'reference',
            'name' => type_annotation($type),
            'arguments' => [],
        ];
    }
    return ['kind' => 'unsupported'];
}

function type_is_optional(Node|Name|string|null $type): bool {
    if ($type instanceof Node\NullableType) {
        return true;
    }
    if ($type instanceof Node\UnionType) {
        return in_array('null', array_map(fn (Node $item): string => strtolower(type_annotation($item)), $type->types), true);
    }
    return false;
}

function attribute_argument(Arg $argument): string {
    $printer = new Standard();
    $value = $printer->prettyPrintExpr($argument->value);
    if ($argument->name !== null) {
        return node_name($argument->name) . ': ' . $value;
    }
    return $argument->unpack ? '...' . $value : $value;
}

function declaration_annotations(Stmt\ClassLike $node): array {
    $annotations = [];
    foreach ($node->attrGroups as $group) {
        foreach ($group->attrs as $attribute) {
            $arguments = array_map(attribute_argument(...), $attribute->args);
            $annotations[] = type_annotation($attribute->name)
                . ($arguments === [] ? '' : '(' . implode(', ', $arguments) . ')');
        }
    }
    return $annotations;
}

function parameter_definitions(array $params): array {
    return array_map(fn (Param $param): array => [
        'name' => var_name($param->var),
        'type' => source_type($param->type),
        'kind' => $param->variadic ? 'variadic_positional' : 'positional',
        'has_default' => $param->default !== null || $param->variadic,
    ], $params);
}

function source_export_entry(string $name, string $kind): array {
    return [
        'name' => $name,
        'local_name' => $name,
        'kind' => $kind,
        'crossing_type' => 'symbol',
        'path' => '',
        'is_relative' => false,
        'normalized_path' => '',
        'is_reexport' => false,
        'is_default' => false,
        'is_aliased' => false,
        'statement_id' => 0,
    ];
}

function source_callable_entry(
    string $sourceId,
    string $name,
    string $qualifiedName,
    ?array $ownerDeclarationId,
    string $kind,
    string $visibility,
    Node $node,
    array $parameters,
    Node|Name|string|null $returnType = null,
    string $declarationKind = 'assignment',
    string $scope = 'module'
): array {
    $family = $kind === 'function'
        ? 'function'
        : (in_array($kind, ['instance_method', 'type_method', 'static_method', 'constructor'], true)
            ? 'method'
            : ($kind === 'callable_value' ? 'value' : 'callable'));
    $entry = [
        'declaration_id' => [
            'source_id' => $sourceId,
            'family' => $family,
            'qualified_name' => $qualifiedName,
            'ordinal' => declaration_ordinal($node),
        ],
        'source_id' => $sourceId,
        'name' => $name,
        'qualified_name' => $qualifiedName,
        'kind' => $kind,
        'visibility' => $visibility,
        'visibility_intent' => visibility_intent($name, $visibility),
        'declaration_annotations' => [],
        'line_start' => $node->getStartLine(),
        'line_end' => $node->getEndLine(),
        'line_count' => line_span($node),
        'parameters' => $parameters,
        'return_type' => source_type($returnType),
        'decorators' => [],
        'docstring' => '',
    ];
    if ($ownerDeclarationId !== null) {
        $entry['owner_declaration_id'] = $ownerDeclarationId;
    }
    if ($kind === 'callable_value') {
        $entry['declaration_kind'] = $declarationKind;
        $entry['value_kind'] = 'value_callable';
        $entry['scope'] = $scope;
    }
    return $entry;
}

function source_value_entry(
    string $sourceId,
    string $name,
    string $visibility,
    Node $node,
    string $declarationKind,
    string $valueKind,
    string $scope
): array {
    return [
        'declaration_id' => [
            'source_id' => $sourceId,
            'family' => 'value',
            'qualified_name' => $name,
            'ordinal' => declaration_ordinal($node),
        ],
        'name' => $name,
        'visibility' => $visibility,
        'visibility_intent' => visibility_intent($name, $visibility),
        'line_count' => line_span($node),
        'declaration_kind' => $declarationKind,
        'value_kind' => $valueKind,
        'scope' => $scope,
    ];
}

function source_property_entry(
    string $sourceId,
    array $ownerDeclarationId,
    string $name,
    Node $node,
    Node|Name|string|null $type,
    bool $isOptional,
    string $visibility,
    string $memberKind
): array {
    return [
        'declaration_id' => [
            'source_id' => $sourceId,
            'family' => 'property',
            'qualified_name' => $ownerDeclarationId['qualified_name'] . '.' . $name,
            'ordinal' => declaration_ordinal($node),
        ],
        'owner_declaration_id' => $ownerDeclarationId,
        'name' => $name,
        'is_optional' => $isOptional,
        'type' => source_type($type),
        'visibility' => $visibility,
        'member_kind' => $memberKind,
        'assigned_values' => [[
            'kind' => 'unsupported',
            'expression' => '',
            'reference' => '',
        ]],
    ];
}

function value_kind(?Expr $expr): string {
    if ($expr === null) {
        return 'value_unknown';
    }
    if ($expr instanceof Expr\Closure || $expr instanceof Expr\ArrowFunction) {
        return 'value_callable';
    }
    if ($expr instanceof Expr\New_ || $expr instanceof Expr\Array_) {
        return 'value_object';
    }
    if ($expr instanceof Node\Scalar || $expr instanceof Expr\ConstFetch) {
        return 'value_literal';
    }
    return 'value_unknown';
}

function expr_name(Node|Name|string|null $expr): string {
    if ($expr instanceof Name || $expr instanceof Node\Identifier) {
        return node_name($expr);
    }
    if ($expr instanceof Stmt\Class_) {
        return $expr->name !== null ? node_name($expr->name) : '';
    }
    if ($expr instanceof Expr\Variable) {
        return '$' . var_name($expr);
    }
    if ($expr instanceof Expr\PropertyFetch) {
        return expr_name($expr->var) . '->' . node_name($expr->name);
    }
    if ($expr instanceof Expr\StaticPropertyFetch) {
        return expr_name($expr->class) . '::$' . node_name($expr->name);
    }
    if ($expr instanceof Expr\MethodCall) {
        return expr_name($expr->var) . '->' . node_name($expr->name);
    }
    if ($expr instanceof Expr\StaticCall) {
        return expr_name($expr->class) . '::' . node_name($expr->name);
    }
    if ($expr instanceof Expr\FuncCall) {
        return expr_name($expr->name);
    }
    if ($expr instanceof Expr\New_) {
        return expr_name($expr->class);
    }
    return '';
}

function expression_target_name(string $expression): string {
    if (str_contains($expression, '->')) {
        $parts = explode('->', $expression);
        return end($parts) ?: $expression;
    }
    if (str_contains($expression, '::')) {
        $parts = explode('::', $expression);
        return ltrim(end($parts) ?: $expression, '$');
    }
    return trim($expression, '$\\');
}

function source_text(Node $node, string $content): string {
    return substr($content, $node->getStartFilePos(), $node->getEndFilePos() - $node->getStartFilePos() + 1);
}

function collect_imports(array $nodes, string $content): array {
    $imports = [];
    $statementId = 0;

    walk_nodes($nodes, function (Node $node, array $parents) use ($content, &$imports, &$statementId): void {
        if (!$node instanceof Stmt\Use_ && !$node instanceof Stmt\GroupUse) {
            return;
        }
        if (!is_top_level($parents)) {
            return;
        }

        $statementId++;
        $prefix = $node instanceof Stmt\GroupUse ? source_text($node->prefix, $content) . '\\' : '';
        foreach ($node->uses as $use) {
            $path = $prefix . source_text($use->name, $content);
            $alias = $use->alias !== null ? node_name($use->alias) : '';
            $symbolName = imported_symbol_name($path);
            $imports[] = [
                'path' => $path,
                'is_relative' => false,
                'normalized_path' => normalize_import_path($path),
                'imported_name' => '',
                'is_aliased' => $alias !== '',
                'crossing_type' => 'symbol',
                'file_barrier_crossed' => true,
                'statement_id' => $statementId,
                'join_key' => import_parent_path($path),
                'uses_joined_import' => count($node->uses) > 1,
                'imported_symbols' => [[
                    'name' => $symbolName,
                    'alias' => $alias,
                    'is_aliased' => $alias !== '',
                    'is_default' => false,
                    'is_namespace' => false,
                    'is_star' => false,
                ]],
            ];
        }
    });

    return $imports;
}

function collect_definitions(array $nodes, string $sourceId): array {
    $classes = [];
    $interfaces = [];
    $traits = [];
    $abstractClasses = [];
    $functions = [];
    $exports = [];
    $classNames = [];
    $inheritance = [];

    walk_nodes($nodes, function (Node $node, array $parents) use (
        $sourceId,
        &$classes,
        &$interfaces,
        &$traits,
        &$abstractClasses,
        &$functions,
        &$exports,
        &$classNames,
        &$inheritance
    ): void {
        if ($node instanceof Stmt\Class_ && $node->name !== null && function_parent($parents) === null) {
            $name = node_name($node->name);
            $family = $node->isAbstract() ? 'abstract_class' : 'class';
            $declarationId = [
                'source_id' => $sourceId,
                'family' => $family,
                'qualified_name' => $name,
                'ordinal' => declaration_ordinal($node),
            ];
            $classNames[spl_object_id($node)] = $name;
            if ($node->extends !== null) {
                $inheritance[] = [
                    'source_declaration_id' => $declarationId,
                    'kind' => 'extends',
                    'target_reference' => node_name($node->extends),
                ];
            }
            foreach ($node->implements as $target) {
                $inheritance[] = [
                    'source_declaration_id' => $declarationId,
                    'kind' => 'implements',
                    'target_reference' => node_name($target),
                ];
            }
            $properties = [];
            foreach ($node->getProperties() as $property) {
                foreach ($property->props as $propertyProperty) {
                    $propertyName = $propertyProperty->name->toString();
                    $properties[$propertyName] = source_property_entry(
                        $sourceId,
                        $declarationId,
                        $propertyName,
                        $propertyProperty,
                        $property->type,
                        $propertyProperty->default instanceof Expr\ConstFetch
                            && strtolower(node_name($propertyProperty->default->name)) === 'null'
                            || type_is_optional($property->type),
                        member_visibility($property),
                        $property->isStatic() ? 'static' : 'instance'
                    );
                }
            }
            foreach ($node->getMethods() as $method) {
                if ($method->name->toString() !== '__construct') {
                    continue;
                }
                foreach ($method->params as $param) {
                    if (($param->flags ?? 0) !== 0) {
                        $propertyName = var_name($param->var);
                        $properties[$propertyName] = source_property_entry(
                            $sourceId,
                            $declarationId,
                            $propertyName,
                            $param,
                            $param->type,
                            $param->default !== null || type_is_optional($param->type),
                            parameter_visibility($param),
                            'instance'
                        );
                    }
                }
            }
            $methods = [];
            $abstractMethods = [];
            $concreteMethods = [];
            foreach ($node->getMethods() as $method) {
                $methodName = $method->name->toString();
                $parameters = parameter_definitions($method->params);
                $entry = source_callable_entry(
                    $sourceId,
                    $methodName,
                    $name . '.' . $methodName,
                    $declarationId,
                    $methodName === '__construct'
                        ? 'constructor'
                        : ($method->isStatic() ? 'static_method' : 'instance_method'),
                    member_visibility($method),
                    $method,
                    $parameters,
                    $method->returnType
                );
                if ($node->isAbstract()) {
                    if ($method->isAbstract()) {
                        $abstractMethods[] = $entry;
                    } else {
                        $concreteMethods[] = $entry;
                    }
                } else {
                    $methods[] = $entry;
                }
            }
            $base = [
                'declaration_id' => $declarationId,
                'kind' => $family,
                'name' => $name,
                'visibility' => class_visibility($node),
                'visibility_intent' => visibility_intent($name, class_visibility($node)),
                'declaration_annotations' => declaration_annotations($node),
                'properties' => array_values($properties),
                'line_count' => line_span($node),
            ];
            if ($node->isAbstract()) {
                $abstractClasses[] = [
                    ...$base,
                    'abstract_methods' => $abstractMethods,
                    'methods' => $concreteMethods,
                ];
                $exports[] = source_export_entry($name, 'abstract_class');
            } else {
                $classes[] = [
                    ...$base,
                    'methods' => $methods,
                ];
                $exports[] = source_export_entry($name, 'class');
            }
            return;
        }

        if ($node instanceof Stmt\Interface_ && function_parent($parents) === null) {
            $name = node_name($node->name);
            $declarationId = [
                'source_id' => $sourceId,
                'family' => 'interface',
                'qualified_name' => $name,
                'ordinal' => declaration_ordinal($node),
            ];
            foreach ($node->extends as $target) {
                $inheritance[] = [
                    'source_declaration_id' => $declarationId,
                    'kind' => 'extends',
                    'target_reference' => node_name($target),
                ];
            }
            $methods = [];
            foreach ($node->getMethods() as $method) {
                $parameters = parameter_definitions($method->params);
                $methodName = $method->name->toString();
                $methods[] = source_callable_entry(
                    $sourceId,
                    $methodName,
                    $name . '.' . $methodName,
                    $declarationId,
                    $method->isStatic() ? 'static_method' : 'instance_method',
                    'public',
                    $method,
                    $parameters,
                    $method->returnType
                );
            }
            $interfaces[] = [
                'declaration_id' => $declarationId,
                'kind' => 'interface',
                'name' => $name,
                'visibility' => 'public',
                'visibility_intent' => visibility_intent($name, 'public'),
                'declaration_annotations' => declaration_annotations($node),
                'methods' => $methods,
                'properties' => [],
                'signatures' => [],
                'line_count' => line_span($node),
            ];
            $exports[] = source_export_entry($name, 'interface');
            return;
        }

        if ($node instanceof Stmt\Trait_ && function_parent($parents) === null) {
            $name = node_name($node->name);
            $declarationId = [
                'source_id' => $sourceId,
                'family' => 'type',
                'qualified_name' => $name,
                'ordinal' => declaration_ordinal($node),
            ];
            $properties = [];
            foreach ($node->getProperties() as $property) {
                foreach ($property->props as $propertyProperty) {
                    $propertyName = $propertyProperty->name->toString();
                    $properties[] = source_property_entry(
                        $sourceId,
                        $declarationId,
                        $propertyName,
                        $propertyProperty,
                        $property->type,
                        $propertyProperty->default instanceof Expr\ConstFetch
                            && strtolower(node_name($propertyProperty->default->name)) === 'null'
                            || type_is_optional($property->type),
                        member_visibility($property),
                        $property->isStatic() ? 'static' : 'instance'
                    );
                }
            }
            $methods = [];
            foreach ($node->getMethods() as $method) {
                $methodName = $method->name->toString();
                $methods[] = source_callable_entry(
                    $sourceId,
                    $methodName,
                    $name . '.' . $methodName,
                    $declarationId,
                    $method->isStatic() ? 'static_method' : 'instance_method',
                    member_visibility($method),
                    $method,
                    parameter_definitions($method->params),
                    $method->returnType
                );
            }
            $traits[] = [
                'declaration_id' => $declarationId,
                'kind' => 'trait',
                'name' => $name,
                'visibility' => 'public',
                'visibility_intent' => visibility_intent($name, 'public'),
                'declaration_annotations' => declaration_annotations($node),
                'methods' => $methods,
                'properties' => $properties,
                'signatures' => [],
                'line_count' => line_span($node),
            ];
            $exports[] = source_export_entry($name, 'type');
            return;
        }

        if ($node instanceof Stmt\Function_ && function_parent($parents) === null) {
            $name = node_name($node->name);
            $exports[] = source_export_entry($name, 'function');
        }
    });

    return [
        'declarations' => [...$classes, ...$interfaces, ...$traits, ...$abstractClasses],
        'functions' => $functions,
        'exports' => $exports,
        'class_names' => $classNames,
        'declaration_relations' => $inheritance,
    ];
}

function callable_name_for_expr(Expr\Closure|Expr\ArrowFunction $node, array $parents): array {
    $parent = $parents[count($parents) - 1] ?? null;
    if ($parent instanceof Expr\Assign && $parent->var instanceof Expr\Variable && is_string($parent->var->name)) {
        return [$parent->var->name, $parent->var->name, '', 'private', $parent];
    }
    if ($parent instanceof Arg) {
        $name = '<anonymous>@' . $node->getStartLine();
        return [$name, $name, '', 'private', $node];
    }
    $name = '<anonymous>@' . $node->getStartLine();
    return [$name, $name, '', 'private', $node];
}

function collect_values_and_callables(array $nodes, string $sourceId): array {
    $values = [];
    $callables = [];
    $callableRanges = [];

    $addCallable = function (array $entry, Node $node, string $ownerName) use (&$callables, &$callableRanges): void {
        $callables[] = $entry;
        $callableRanges[spl_object_id($node)] = [
            'declarationId' => $entry['declaration_id'],
            'ownerName' => $ownerName,
            'node' => $node,
        ];
    };

    walk_nodes($nodes, function (Node $node, array $parents) use (
        $sourceId,
        &$values,
        $addCallable
    ): void {
        if ($node instanceof Expr\Assign && $node->var instanceof Expr\Variable && is_string($node->var->name)) {
            if (!$node->expr instanceof Expr\Closure && !$node->expr instanceof Expr\ArrowFunction) {
                $values[] = source_value_entry(
                    $sourceId,
                    $node->var->name,
                    'private',
                    $node,
                    'assignment',
                    value_kind($node->expr),
                    function_parent($parents) === null ? 'module' : 'local'
                );
            }
        }

        if ($node instanceof Stmt\Const_) {
            foreach ($node->consts as $const) {
                $values[] = source_value_entry(
                    $sourceId,
                    $const->name->toString(),
                    'public',
                    $const,
                    'constant',
                    value_kind($const->value),
                    'module'
                );
            }
        }

        if ($node instanceof Stmt\ClassConst) {
            foreach ($node->consts as $const) {
                $values[] = source_value_entry(
                    $sourceId,
                    $const->name->toString(),
                    member_visibility($node),
                    $const,
                    'constant',
                    value_kind($const->value),
                    'member'
                );
            }
        }

        if ($node instanceof Stmt\Function_) {
            $name = node_name($node->name);
            $addCallable(source_callable_entry(
                $sourceId,
                $name,
                $name,
                null,
                'function',
                'public',
                $node,
                parameter_definitions($node->params),
                $node->returnType
            ), $node, '');
            return;
        }

        if ($node instanceof Stmt\ClassMethod && !$node->isAbstract()) {
            $owner = nearest_parent($parents, Stmt\Class_::class, Stmt\Trait_::class);
            $ownerName = $owner instanceof Stmt\ClassLike && $owner->name !== null ? node_name($owner->name) : '';
            $ownerDeclarationId = $owner instanceof Stmt\ClassLike && $owner->name !== null
                ? [
                    'source_id' => $sourceId,
                    'family' => $owner instanceof Stmt\Trait_
                        ? 'type'
                        : ($owner->isAbstract() ? 'abstract_class' : 'class'),
                    'qualified_name' => $ownerName,
                    'ordinal' => declaration_ordinal($owner),
                ]
                : null;
            $name = node_name($node->name);
            $kind = $name === '__construct' ? 'constructor' : ($node->isStatic() ? 'static_method' : 'instance_method');
            $addCallable(source_callable_entry(
                $sourceId,
                $name,
                $ownerName !== '' ? $ownerName . '.' . $name : $name,
                $ownerDeclarationId,
                $kind,
                member_visibility($node),
                $node,
                parameter_definitions($node->params),
                $node->returnType
            ), $node, $ownerName);
            return;
        }

        if ($node instanceof Expr\Closure || $node instanceof Expr\ArrowFunction) {
            [$name, $qualifiedName, $ownerName, $visibility, $startNode] = callable_name_for_expr($node, $parents);
            $addCallable(source_callable_entry(
                $sourceId,
                $name,
                $qualifiedName,
                null,
                str_starts_with($name, '<anonymous>@') ? 'anonymous' : 'callable_value',
                $visibility,
                $startNode,
                parameter_definitions($node->params),
                $node->returnType,
                'assignment',
                function_parent($parents) === null ? 'module' : 'local'
            ), $node, $ownerName);
        }
    });

    return [
        'values' => $values,
        'callables' => $callables,
        'callable_ranges' => $callableRanges,
    ];
}

function collect_calls(array $nodes, string $sourceId, array $callables, array $callableRanges): array {
    $calls = [];
    $nextOrdinalByOwner = array_fill_keys(array_keys($callableRanges), 1);
    $byName = [];
    $byQualifiedName = [];
    $constructorsByName = [];

    foreach ($callables as $callable) {
        $byQualifiedName[$callable['qualified_name']][] = $callable['declaration_id'];
        if (in_array($callable['kind'], ['function', 'callable_value'], true)) {
            $byName[$callable['name']][] = $callable['declaration_id'];
        }
        if ($callable['kind'] === 'constructor') {
            $ownerName = $callable['owner_declaration_id']['qualified_name'];
            $constructorsByName[$ownerName][] = $callable['declaration_id'];
        }
    }

    walk_nodes($nodes, function (Node $node, array $parents) use (
        &$calls,
        &$nextOrdinalByOwner,
        $sourceId,
        $callableRanges,
        $byName,
        $byQualifiedName,
        $constructorsByName
    ): void {
        $expression = '';
        $isConstructor = false;
        if ($node instanceof Expr\FuncCall) {
            $expression = expr_name($node->name);
        } elseif ($node instanceof Expr\MethodCall) {
            $expression = expr_name($node);
        } elseif ($node instanceof Expr\StaticCall) {
            $expression = expr_name($node);
        } elseif ($node instanceof Expr\New_) {
            $expression = expr_name($node->class);
            $isConstructor = true;
        } else {
            return;
        }

        $owner = function_parent($parents);
        if ($owner === null) {
            return;
        }
        $range = $callableRanges[spl_object_id($owner)] ?? null;
        if ($range === null || $expression === '') {
            return;
        }

        $ownerId = spl_object_id($owner);
        $ordinal = $nextOrdinalByOwner[$ownerId];
        $nextOrdinalByOwner[$ownerId] = $ordinal + 1;

        $targetCallableId = null;
        $resolution = 'unresolved';
        if ($isConstructor && count($constructorsByName[$expression] ?? []) === 1) {
            $targetCallableId = $constructorsByName[$expression][0];
            $resolution = 'resolved';
        } elseif (count($byQualifiedName[$expression] ?? []) === 1) {
            $targetCallableId = $byQualifiedName[$expression][0];
            $resolution = 'resolved';
        } elseif (str_starts_with($expression, '$this->') && $range['ownerName'] !== '') {
            $qualifiedName = $range['ownerName'] . '.' . substr($expression, strlen('$this->'));
            if (count($byQualifiedName[$qualifiedName] ?? []) === 1) {
                $targetCallableId = $byQualifiedName[$qualifiedName][0];
                $resolution = 'resolved';
            }
        } elseif (count($byName[$expression] ?? []) === 1) {
            $targetCallableId = $byName[$expression][0];
            $resolution = 'resolved';
        }

        $calls[] = [
            'source_callable_id' => $range['declarationId'],
            'ordinal' => $ordinal,
            'target_callable_id' => $targetCallableId,
            'source_id' => $sourceId,
            'line' => $node->getStartLine(),
            'expression' => $expression,
            'resolution' => $resolution,
            'target_name' => expression_target_name($expression),
        ];
    });

    return $calls;
}

function extract_file(string $path, ?string $sourceId = null, ?string $sourcesRoot = null): array {
    $content = file_get_contents($path);
    if ($content === false) {
        fwrite(STDERR, "Unable to read PHP file: {$path}\n");
        exit(1);
    }

    try {
        $nodes = (new ParserFactory())->createForHostVersion()->parse($content) ?? [];
    } catch (Error $error) {
        if ($error->getStartLine() < 1 || !$error->hasColumnInfo()) {
            throw new LogicException("PHP parser omitted the source parse location for {$path}.", previous: $error);
        }
        $failure = [
            'code' => 'source_parse',
            'language' => 'php',
            'path' => $path,
            'line' => $error->getStartLine(),
            'column' => $error->getStartColumn($content),
            'diagnostic' => $error->getRawMessage(),
        ];
        fwrite(STDERR, 'modwire-error:' . json_encode($failure, JSON_THROW_ON_ERROR) . "\n");
        exit(1);
    }

    $root = $sourcesRoot ?? dirname($path);
    $resolvedSourceId = $sourceId ?? source_id_for_path($path, $root);
    $definitions = collect_definitions($nodes, $resolvedSourceId);
    $graph = collect_values_and_callables($nodes, $resolvedSourceId);

    return [
        'imports' => collect_imports($nodes, $content),
        'exports' => $definitions['exports'],
        'namespaces' => [],
        'declarations' => $definitions['declarations'],
        'functions' => array_values(array_filter(
            $graph['callables'],
            fn (array $callable): bool => $callable['kind'] === 'function'
        )),
        'values' => $graph['values'],
        'callable_values' => array_values(array_filter(
            $graph['callables'],
            fn (array $callable): bool => $callable['kind'] === 'callable_value'
        )),
        'anonymous_callables' => array_values(array_filter(
            $graph['callables'],
            fn (array $callable): bool => $callable['kind'] === 'anonymous'
        )),
        'calls' => collect_calls($nodes, $resolvedSourceId, $graph['callables'], $graph['callable_ranges']),
        'declaration_relations' => $definitions['declaration_relations'],
        'line_count' => line_count_for_content($content),
        'code_line_count' => code_line_count_for_content($content),
        'public_symbol_count' => count($definitions['exports']),
    ];
}

function extract_batch_from_stdin(string $sourcesRoot): array {
    $pathsBySourceId = json_decode(stream_get_contents(STDIN), true);
    if (!is_array($pathsBySourceId)) {
        fwrite(STDERR, "Expected a JSON object mapping source ids to PHP file paths.\n");
        exit(1);
    }

    $result = [];
    foreach ($pathsBySourceId as $sourceId => $path) {
        if (!is_string($sourceId) || !is_string($path)) {
            fwrite(STDERR, "Expected source ids and paths to be strings.\n");
            exit(1);
        }
        $result[$sourceId] = extract_file($path, $sourceId, $sourcesRoot);
    }
    return $result;
}

function write_batch_jsonl_from_stdin(string $sourcesRoot): void {
    $pathsBySourceId = json_decode(stream_get_contents(STDIN), true);
    if (!is_array($pathsBySourceId)) {
        fwrite(STDERR, "Expected a JSON object mapping source ids to PHP file paths.\n");
        exit(1);
    }

    foreach ($pathsBySourceId as $sourceId => $path) {
        if (!is_string($sourceId) || !is_string($path)) {
            fwrite(STDERR, "Expected source ids and paths to be strings.\n");
            exit(1);
        }
        echo json_encode([
            $sourceId,
            extract_file($path, $sourceId, $sourcesRoot),
        ]) . "\n";
    }
}

if (($argv[1] ?? null) === '--batch') {
    if (in_array('--jsonl', $argv, true)) {
        write_batch_jsonl_from_stdin($argv[2] ?? getcwd());
    } else {
        echo json_encode(extract_batch_from_stdin($argv[2] ?? getcwd()));
    }
} else {
    echo json_encode(extract_file($argv[1], null, $argv[2] ?? dirname($argv[1])));
}
