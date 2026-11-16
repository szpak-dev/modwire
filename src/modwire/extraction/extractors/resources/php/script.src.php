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

function function_parent(array $parents): ?Node {
    return nearest_parent(
        $parents,
        Stmt\ClassMethod::class,
        Stmt\Function_::class,
        Expr\Closure::class,
        Expr\ArrowFunction::class,
    );
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

final class PhpExtractorInvariantFailure extends RuntimeException {}

final class PhpStructuralIndex {
    public array $identities = [];
    public array $identitiesByQualifiedName = [];
    public array $parents = [];
    public array $scopes = [];
    public array $namespaces = [];
    public array $limitations = [];

    public function __construct(public readonly string $sourceId, public readonly string $contentDigest, array $nodes) {
        walk_nodes($nodes, function (Node $node, array $parents): void {
            $this->parents[spl_object_id($node)] = $parents;
            if ($node instanceof Stmt\Foreach_ || $node instanceof Stmt\Catch_ || $node instanceof Expr\AssignRef ||
                ($node instanceof Expr\Assign && !($node->var instanceof Expr\Variable && is_string($node->var->name)))) {
                $this->limit('values', $node, 'Binding target is not represented as a named source value.');
                $this->limit('callable_values', $node, 'Callable ownership of this binding is not represented.');
            }
            $family = null;
            $name = '';
            if ($node instanceof Stmt\Namespace_) {
                $family = 'namespace';
                $name = $node->name === null ? '<global>' : str_replace('\\', '.', $node->name->toString());
            } elseif ($node instanceof Stmt\ClassLike) {
                $family = $node instanceof Stmt\Interface_ ? 'interface' : ($node instanceof Stmt\Trait_ ? 'type' : (($node instanceof Stmt\Class_ && $node->isAbstract()) ? 'abstract_class' : 'class'));
                $name = $node->name === null ? '<anonymous>@' . declaration_ordinal($node) : $node->name->toString();
            } elseif ($node instanceof Stmt\ClassMethod || $node instanceof Stmt\Function_) {
                $family = $node instanceof Stmt\ClassMethod ? 'method' : 'function';
                $name = $node->name->toString();
            } elseif ($node instanceof Expr\Closure || $node instanceof Expr\ArrowFunction) {
                $parent = $parents === [] ? null : $parents[count($parents)-1];
                $bound = $parent instanceof Expr\Assign && $parent->var instanceof Expr\Variable && is_string($parent->var->name);
                $family = $bound ? 'value' : 'callable';
                $name = $bound ? $parent->var->name : '<anonymous>@' . declaration_ordinal($node);
            }
            if ($family !== null) {
                $owner = $this->nearestIdentity($parents);
                $qualified = $owner === null || $family === 'namespace' ? $name : $owner['qualified_name'] . '.' . $name;
                $this->identities[spl_object_id($node)] = $this->createIdentity($family, $qualified, $node);
                $this->scopes[spl_object_id($node)] = $this->identities[spl_object_id($node)];
                if ($node instanceof Stmt\Namespace_) {
                    $this->namespaces[] = ['kind' => 'namespace', 'declaration_id' => $this->identities[spl_object_id($node)],
                        'placement' => $this->placement($node)];
                }
            } elseif ($node instanceof Expr\Assign && $node->var instanceof Expr\Variable && is_string($node->var->name) &&
                !($node->expr instanceof Expr\Closure || $node->expr instanceof Expr\ArrowFunction)) {
                $this->identities[spl_object_id($node)] = $this->createIdentity('value', $this->qualifiedName($node->var->name, $node), $node);
            } elseif ($node instanceof Node\Const_) {
                $this->identities[spl_object_id($node)] = $this->createIdentity('value', $this->qualifiedName($node->name->toString(), $node), $node);
            }
        });
        foreach ($this->identities as $key => $identity) {
            $this->identitiesByQualifiedName[$identity['qualified_name']][] = $key;
        }
    }

    public function createIdentity(string $family, string $name, Node $node): array {
        return ['source_id' => $this->sourceId, 'content_digest' => $this->contentDigest,
            'family' => $family, 'qualified_name' => $name, 'ordinal' => declaration_ordinal($node)];
    }

    public function qualifiedName(string $name, Node $node): string {
        $owner = $this->nearestIdentity($this->parents[spl_object_id($node)]);
        return $owner === null ? $name : $owner['qualified_name'] . '.' . $name;
    }

    public function limit(string $family, Node $node, string $description): void {
        $this->limitations[$family][] = ['kind' => 'unsupported_syntax', 'description' => $description,
            'location' => ['kind' => 'source', 'start_line' => $node->getStartLine(), 'end_line' => $node->getEndLine()]];
    }

    public function nearestIdentity(array $parents): ?array {
        foreach (array_reverse($parents) as $parent) {
            if (isset($this->scopes[spl_object_id($parent)])) return $this->scopes[spl_object_id($parent)];
        }
        return null;
    }

    public function placement(Node $node): array {
        $parents = $this->parents[spl_object_id($node)];
        $parent = $this->nearestIdentity($parents);
        $scope = $parent === null ? ['kind' => 'file'] : ['kind' => 'declaration', 'declaration_id' => $parent];
        $namespace = ['kind' => 'none'];
        foreach (array_reverse($parents) as $ancestor) {
            if ($ancestor instanceof Stmt\Namespace_) {
                $identity = $this->identities[spl_object_id($ancestor)];
                $namespace = ['kind' => 'member', 'namespace_reference' => $identity['qualified_name'],
                    'target' => ['kind' => 'resolved', 'declaration_id' => $identity]];
                break;
            }
        }
        return ['lexical_scope' => $scope, 'namespace' => $namespace];
    }

    public function resolve(string $reference, Node $source): array {
        $name = str_replace('\\', '.', ltrim($reference, '\\'));
        $scope = $this->nearestIdentity($this->parents[spl_object_id($source)]);
        $prefix = $scope === null ? '' : $scope['qualified_name'];
        while (true) {
            $qualified = $prefix === '' || str_starts_with($reference, '\\') ? $name : $prefix . '.' . $name;
            $matches = $this->identitiesByQualifiedName[$qualified] ?? [];
            if (count($matches) === 1) return ['kind' => 'resolved', 'declaration_id' => $this->identities[$matches[0]]];
            if (count($matches) > 1) return ['kind' => 'unresolved', 'reason' => 'ambiguous'];
            if ($prefix === '') return ['kind' => 'unresolved', 'reason' => 'external'];
            $separator = strrpos($prefix, '.');
            $prefix = $separator === false ? '' : substr($prefix, 0, $separator);
        }
    }
}

function inventory_coverage(array $limitations = [], string $status = 'complete'): array {
    return ['status' => $limitations === [] ? $status : 'incomplete', 'limitations' => $limitations];
}

function member_inventory(): array {
    return ['methods' => inventory_coverage(), 'abstract_methods' => inventory_coverage(),
        'properties' => inventory_coverage(), 'signatures' => inventory_coverage([], 'not_applicable')];
}

function source_export_entry(string $name, string $kind, array $identity): array {
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
        'binding' => ['kind' => 'resolved', 'declaration_ids' => [$identity]],
    ];
}

function source_callable_entry(
    PhpStructuralIndex $index,
    string $name,
    ?array $ownerDeclarationId,
    string $kind,
    string $visibility,
    Node $node,
    array $parameters,
    Node|Name|string|null $returnType = null,
    string $declarationKind = 'assignment',
    string $scope = 'module'
): array {
    $entry = [
        'declaration_id' => $index->identities[spl_object_id($node)],
        'source_id' => $index->sourceId,
        'placement' => $index->placement($node),
        'name' => $name,
        'qualified_name' => $index->identities[spl_object_id($node)]['qualified_name'],
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
    PhpStructuralIndex $index,
    string $name,
    string $visibility,
    Node $node,
    string $declarationKind,
    string $valueKind,
    string $scope
): array {
    return [
        'declaration_id' => $index->identities[spl_object_id($node)],
        'placement' => $index->placement($node),
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
    PhpStructuralIndex $index,
    array $ownerDeclarationId,
    string $name,
    Node $node,
    Node|Name|string|null $type,
    bool $isOptional,
    string $visibility,
    string $memberKind
): array {
    return [
        'declaration_id' => $index->createIdentity('property', $ownerDeclarationId['qualified_name'] . '.' . $name, $node),
        'owner_declaration_id' => $ownerDeclarationId,
        'placement' => $index->placement($node),
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

function collect_imports(array $nodes, string $content, PhpStructuralIndex $index): array {
    $imports = [];
    $statementId = 0;

    walk_nodes($nodes, function (Node $node, array $parents) use ($content, $index, &$imports, &$statementId): void {
        if (!$node instanceof Stmt\Use_ && !$node instanceof Stmt\GroupUse) {
            return;
        }
        $scope = $index->nearestIdentity($index->parents[spl_object_id($node)]);
        if ($scope !== null && $scope['family'] !== 'namespace') {
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

function collect_definitions(array $nodes, PhpStructuralIndex $index, array $callables): array {
    $declarations = [];
    $exports = [];
    $relations = [];
    walk_nodes($nodes, function (Node $node, array $parents) use ($index, $callables, &$declarations, &$exports, &$relations): void {
        if ($node instanceof Stmt\Function_) {
            $identity = $index->identities[spl_object_id($node)];
            $exports[] = source_export_entry($identity['qualified_name'], 'function', $identity);
            return;
        }
        if (!$node instanceof Stmt\ClassLike) return;
        $identity = $index->identities[spl_object_id($node)];
        $kind = $node instanceof Stmt\Trait_ ? 'trait' : ($node instanceof Stmt\Enum_ ? 'enum' : $identity['family']);
        $properties = [];
        foreach ($node->stmts as $member) {
            if ($member instanceof Stmt\Property) {
                foreach ($member->props as $property) {
                    $properties[] = source_property_entry($index, $identity, $property->name->toString(), $property,
                        $member->type, type_is_optional($member->type), member_visibility($member), $member->isStatic() ? 'static' : 'instance');
                }
            } elseif ($member instanceof Stmt\ClassMethod) {
                foreach ($member->params as $parameter) {
                    if ($parameter->flags !== 0 && $parameter->var instanceof Expr\Variable && is_string($parameter->var->name)) {
                        $properties[] = source_property_entry($index, $identity, $parameter->var->name, $parameter,
                            $parameter->type, type_is_optional($parameter->type), parameter_visibility($parameter), 'instance');
                    }
                }
            } elseif ($member instanceof Stmt\TraitUse) {
                foreach ($member->traits as $trait) $relations[] = ['source_declaration_id' => $identity,
                    'kind' => 'uses_trait', 'target_reference' => $trait->toString(), 'target' => $index->resolve($trait->toString(), $node)];
            }
        }
        $methods = [];
        $abstract = [];
        foreach ($node->getMethods() as $method) {
            $methodId = $index->identities[spl_object_id($method)];
            foreach ($callables as $callable) {
                if ($callable['declaration_id'] === $methodId) {
                    if ($method->isAbstract() || $node instanceof Stmt\Interface_) $abstract[] = $callable;
                    else $methods[] = $callable;
                }
            }
        }
        $targets = [];
        if ($node instanceof Stmt\Class_) {
            if ($node->extends !== null) $targets[] = ['extends', $node->extends];
            foreach ($node->implements as $target) $targets[] = ['implements', $target];
        } elseif ($node instanceof Stmt\Interface_) {
            foreach ($node->extends as $target) $targets[] = ['extends', $target];
        } elseif ($node instanceof Stmt\Enum_) {
            foreach ($node->implements as $target) $targets[] = ['implements', $target];
        }
        foreach ($targets as [$relationKind, $target]) $relations[] = ['source_declaration_id' => $identity,
            'kind' => $relationKind, 'target_reference' => $target->toString(), 'target' => $index->resolve($target->toString(), $node)];
        $declarations[] = ['declaration_id' => $identity, 'kind' => $kind, 'name' => $identity['qualified_name'],
            'visibility' => 'public', 'visibility_intent' => 'public', 'declaration_annotations' => declaration_annotations($node),
            'line_count' => line_span($node), 'methods' => $methods, 'abstract_methods' => $abstract, 'properties' => $properties,
            'signatures' => [], 'inventory' => member_inventory(), 'placement' => $index->placement($node)];
        if ($node->name !== null) $exports[] = source_export_entry($identity['qualified_name'],
            in_array($kind, ['trait', 'enum'], true) ? 'type' : $kind, $identity);
    });
    return ['declarations' => $declarations, 'exports' => $exports, 'declaration_relations' => $relations];
}

function collect_values_and_callables(array $nodes, PhpStructuralIndex $index): array {
    $values = [];
    $callables = [];
    $callableRanges = [];

    $addCallable = function (array $entry, Node $node) use (&$callables, &$callableRanges): void {
        $callables[] = $entry;
        $callableRanges[spl_object_id($node)] = $entry['declaration_id'];
    };

    walk_nodes($nodes, function (Node $node, array $parents) use (
        $index,
        &$values,
        $addCallable
    ): void {
        if ($node instanceof Expr\Assign && $node->var instanceof Expr\Variable && is_string($node->var->name)) {
            if (!$node->expr instanceof Expr\Closure && !$node->expr instanceof Expr\ArrowFunction) {
                $values[] = source_value_entry(
                    $index,
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
                    $index,
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
                    $index,
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
                $index,
                $name,
                null,
                'function',
                'public',
                $node,
                parameter_definitions($node->params),
                $node->returnType
            ), $node);
            return;
        }

        if ($node instanceof Stmt\ClassMethod) {
            $owner = nearest_parent($parents, Stmt\ClassLike::class);
            if (!$owner instanceof Stmt\ClassLike) throw new PhpExtractorInvariantFailure('PHP method has no native class owner.');
            $ownerDeclarationId = $index->identities[spl_object_id($owner)];
            $name = node_name($node->name);
            $kind = $name === '__construct' ? 'constructor' : ($node->isStatic() ? 'static_method' : 'instance_method');
            $addCallable(source_callable_entry(
                $index,
                $name,
                $ownerDeclarationId,
                $kind,
                member_visibility($node),
                $node,
                parameter_definitions($node->params),
                $node->returnType
            ), $node);
            return;
        }

        if ($node instanceof Expr\Closure || $node instanceof Expr\ArrowFunction) {
            $parent = $parents[count($parents) - 1];
            $bound = $parent instanceof Expr\Assign && $parent->var instanceof Expr\Variable && is_string($parent->var->name);
            $name = $bound ? $parent->var->name : '<anonymous>@' . declaration_ordinal($node);
            $addCallable(source_callable_entry(
                $index,
                $name,
                null,
                $bound ? 'callable_value' : 'anonymous',
                'private',
                $node,
                parameter_definitions($node->params),
                $node->returnType,
                'assignment',
                function_parent($parents) === null ? 'module' : 'local'
            ), $node);
        }
    });

    return [
        'values' => $values,
        'callables' => $callables,
        'callable_ranges' => $callableRanges,
    ];
}

function collect_calls(array $nodes, PhpStructuralIndex $index, array $callables, array $callableRanges): array {
    $calls = [];
    $nextOrdinalByOwner = array_fill_keys(array_keys($callableRanges), 1);
    walk_nodes($nodes, function (Node $node, array $parents) use (&$calls, &$nextOrdinalByOwner, $index, $callableRanges, $callables): void {
        if (!$node instanceof Expr\FuncCall && !$node instanceof Expr\MethodCall && !$node instanceof Expr\NullsafeMethodCall && !$node instanceof Expr\StaticCall && !$node instanceof Expr\New_) return;
        $owner = function_parent($parents);
        if ($owner === null) return;
        $range = $callableRanges[spl_object_id($owner)];
        $expression = $node instanceof Expr\FuncCall ? expr_name($node->name) : ($node instanceof Expr\New_ ? expr_name($node->class) : expr_name($node));
        $reference = $expression;
        $dynamic = false;
        if ($node instanceof Expr\MethodCall || $node instanceof Expr\NullsafeMethodCall) {
            $class = nearest_parent($parents, Stmt\ClassLike::class);
            if ($class !== null && $node->var instanceof Expr\Variable && $node->var->name === 'this' && $node->name instanceof Node\Identifier) {
                $reference = '\\' . $index->identities[spl_object_id($class)]['qualified_name'] . '.' . $node->name->toString();
            } else $dynamic = true;
        } elseif ($node instanceof Expr\StaticCall) {
            if ($node->class instanceof Name && $node->name instanceof Node\Identifier) {
                $class = nearest_parent($parents, Stmt\ClassLike::class);
                $reference = $node->class->toString();
                if ($reference === 'self' && $class !== null) $reference = '\\' . $index->identities[spl_object_id($class)]['qualified_name'];
                elseif (in_array($reference, ['static', 'parent'], true)) $dynamic = true;
                $reference .= '.' . $node->name->toString();
            } else $dynamic = true;
        } elseif ($node instanceof Expr\FuncCall && $node->name instanceof Expr\Variable && is_string($node->name->name)) {
            $reference = $node->name->name;
        } elseif ($node instanceof Expr\FuncCall && !$node->name instanceof Name) $dynamic = true;
        elseif ($node instanceof Expr\New_ && !$node->class instanceof Name) $dynamic = true;
        $target = $dynamic ? ['kind' => 'unresolved', 'reason' => 'dynamic'] : $index->resolve($reference, $node);
        $candidates = [];
        if ($target['kind'] === 'resolved') foreach ($callables as $callable) {
            if ($node instanceof Expr\New_) {
                if ($callable['kind'] === 'constructor' && $callable['owner_declaration_id'] === $target['declaration_id']) $candidates[] = $callable['declaration_id'];
            } elseif ($callable['declaration_id'] === $target['declaration_id']) $candidates[] = $callable['declaration_id'];
        }
        $calls[] = ['source_callable_id' => $range, 'ordinal' => $nextOrdinalByOwner[spl_object_id($owner)]++,
            'target_callable_id' => count($candidates) === 1 ? $candidates[0] : null, 'source_id' => $index->sourceId,
            'line' => $node->getStartLine(), 'expression' => $expression === '' ? (new Standard())->prettyPrintExpr($node) : $expression,
            'resolution' => count($candidates) === 1 ? 'resolved' : ($dynamic ? 'dynamic' : 'unresolved'), 'target_name' => expression_target_name($expression)];
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
            throw new PhpExtractorInvariantFailure("PHP parser omitted the source parse location for {$path}.", previous: $error);
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
    $index = new PhpStructuralIndex($resolvedSourceId, hash('sha256', $content), $nodes);
    $graph = collect_values_and_callables($nodes, $index);
    $definitions = collect_definitions($nodes, $index, $graph['callables']);
    foreach ($graph['values'] as $value) {
        if ($value['declaration_kind'] === 'constant' && $value['scope'] === 'module') {
            $definitions['exports'][] = source_export_entry($value['name'], 'value', $value['declaration_id']);
        }
    }
    $inventory = [];
    foreach (['declarations', 'functions', 'values', 'callable_values', 'anonymous_callables', 'namespaces', 'exports'] as $family) $inventory[$family] = inventory_coverage($index->limitations[$family] ?? []);
    $inventory['unresolved_methods'] = inventory_coverage([], 'not_applicable');

    return [
        'imports' => collect_imports($nodes, $content, $index),
        'exports' => $definitions['exports'],
        'namespaces' => $index->namespaces,
        'inventory' => $inventory,
        'unresolved_methods' => [],
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
        'calls' => collect_calls($nodes, $index, $graph['callables'], $graph['callable_ranges']),
        'declaration_relations' => $definitions['declaration_relations'],
        'line_count' => line_count_for_content($content),
        'code_line_count' => code_line_count_for_content($content),
        'public_symbol_count' => count($definitions['exports']),
    ];
}

function write_batch_from_stdin(string $sourcesRoot): void {
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
        fflush(STDOUT);
    }
}

if (($argv[1] ?? null) === '--batch') {
    write_batch_from_stdin($argv[2] ?? getcwd());
} else {
    echo json_encode(extract_file($argv[1], null, $argv[2] ?? dirname($argv[1])));
}
