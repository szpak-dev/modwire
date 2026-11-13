#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { Project, ScriptKind, ts } from 'ts-morph';

type Family = 'class' | 'abstract_class' | 'interface' | 'type' | 'namespace' | 'function' | 'method' | 'property' | 'value' | 'callable';
type CallableKind = 'function' | 'instance_method' | 'static_method' | 'constructor' | 'callable_value' | 'anonymous';
interface Identity { source_id: string; content_digest: string; family: Family; qualified_name: string; ordinal: number }
type Target = { kind: 'resolved'; declaration_id: Identity } | { kind: 'unresolved'; reason: 'external' | 'dynamic' | 'ambiguous' | 'unobserved' };
type Container = { kind: 'file' } | { kind: 'declaration'; declaration_id: Identity };
type Scope = Container | { kind: 'block'; container: Container; start_utf8_offset: number; end_utf8_offset: number };
interface Placement { lexical_scope: Scope; namespace: { kind: 'none' } | { kind: 'member'; namespace_reference: string; target: Target } }
type SourceType = { kind: 'absent' | 'unsupported' } | { kind: 'reference'; name: string; arguments: SourceType[] };
interface Parameter { name: string; type: SourceType; kind: 'positional' | 'variadic_positional'; has_default: boolean }
interface Limitation { kind: 'unsupported_syntax' | 'dynamic_structure' | 'unresolved_ownership'; location: { kind: 'source'; start_line: number; end_line: number }; description: string }
interface Coverage { status: 'complete' | 'incomplete' | 'not_applicable'; limitations: Limitation[] }
interface Callable { declaration_id: Identity; source_id: string; name: string; qualified_name: string; kind: CallableKind; visibility: string; visibility_intent: string; declaration_annotations: string[]; line_start: number; line_end: number; line_count: number; parameters: Parameter[]; return_type: SourceType; decorators: string[]; docstring: string; placement: Placement; owner_declaration_id?: Identity; owner?: { kind: 'unresolved'; reason: 'dynamic' }; receiver_reference?: string; declaration_kind?: string; value_kind?: string; scope?: string }
interface Property { declaration_id: Identity; owner_declaration_id: Identity; name: string; type: SourceType; is_optional: boolean; visibility: string; member_kind: string; placement: Placement; assigned_values: { kind: string; expression: string; reference: string }[] }
interface Signature { kind: 'call' | 'construct' | 'index'; line_count: number; declared_args: number; optional_args: number }
interface Declaration { declaration_id: Identity; kind: string; name: string; visibility: string; visibility_intent: string; declaration_annotations: string[]; line_count: number; methods: Callable[]; abstract_methods: Callable[]; properties: Property[]; signatures: Signature[]; inventory: Record<string, Coverage>; placement: Placement }
interface Value { declaration_id: Identity; name: string; visibility: string; visibility_intent: string; line_count: number; declaration_kind: string; value_kind: string; scope: string; placement: Placement }
interface Namespace { kind: 'namespace' | 'module'; declaration_id: Identity; placement: Placement }
interface Export { name: string; local_name: string; kind: string; crossing_type: string; path: string; is_relative: boolean; normalized_path: string; is_reexport: boolean; is_default: boolean; is_aliased: boolean; statement_id: number; binding: { kind: 'resolved'; declaration_ids: Identity[] } | { kind: 'unresolved'; reason: 'external' | 'dynamic' | 'ambiguous' | 'unobserved' } }
interface Import { path: string; is_relative: boolean; normalized_path: string; imported_name: string; is_aliased: boolean; crossing_type: string; file_barrier_crossed: boolean; statement_id: number; join_key: string; uses_joined_import: boolean; imported_symbols: { name: string; alias: string; is_aliased: boolean; is_default: boolean; is_namespace: boolean; is_star: boolean }[] }
interface Call { source_callable_id: Identity; ordinal: number; target_callable_id: Identity | null; source_id: string; line: number; expression: string; resolution: string; target_name: string }
interface Relation { source_declaration_id: Identity; kind: string; target_reference: string; target: Target }
interface ExtractedFile { imports: Import[]; exports: Export[]; namespaces: Namespace[]; declarations: Declaration[]; functions: Callable[]; values: Value[]; callable_values: Callable[]; anonymous_callables: Callable[]; unresolved_methods: Callable[]; calls: Call[]; declaration_relations: Relation[]; inventory: Record<string, Coverage>; line_count: number; code_line_count: number; public_symbol_count: number }
type CallableNode = ts.FunctionDeclaration | ts.FunctionExpression | ts.ArrowFunction | ts.MethodDeclaration | ts.MethodSignature | ts.ConstructorDeclaration | ts.GetAccessorDeclaration | ts.SetAccessorDeclaration;
type DeclarationNode = ts.ClassDeclaration | ts.ClassExpression | ts.InterfaceDeclaration | ts.TypeAliasDeclaration | ts.EnumDeclaration;

class SourceParseFailure extends Error {
    constructor(readonly sourcePath: string, readonly line: number, readonly column: number, readonly diagnostic: string) { super(diagnostic); }
}
class SourceInvariantFailure extends Error {}
class InputContractFailure extends Error {}

class TypeScriptExtractor {
    readonly source: ts.SourceFile;
    readonly digest: string;
    readonly identities = new Map<ts.Node, Identity>();
    readonly containers = new Map<ts.Node, ts.Node>();
    readonly callableNodes = new Map<CallableNode, CallableKind>();
    readonly declarationNodes = new Map<DeclarationNode, string>();
    readonly aliasTypes = new Map<ts.TypeAliasDeclaration, ts.TypeNode>();
    readonly declarations = new Map<ts.Node, Declaration>();
    readonly callables = new Map<ts.Node, Callable>();
    readonly inventory: Record<string, Coverage> = {};
    readonly imports: Import[] = [];
    readonly exports: Export[] = [];
    readonly values: Value[] = [];
    readonly namespaces: Namespace[] = [];
    readonly relations: Relation[] = [];

    constructor(readonly sourceId: string, readonly filePath: string, readonly root: string, readonly content: string) {
        const project = new Project({ useInMemoryFileSystem: true, skipLoadingLibFiles: true,
            compilerOptions: { allowJs: true, target: ts.ScriptTarget.ESNext, jsx: ts.JsxEmit.Preserve } });
        const extension = path.extname(filePath).toLowerCase();
        const scriptKind = extension === '.tsx' ? ScriptKind.TSX : extension === '.jsx' ? ScriptKind.JSX : extension === '.js' ? ScriptKind.JS : ScriptKind.TS;
        const file = project.createSourceFile(filePath, content, { scriptKind });
        this.source = file.compilerNode;
        const diagnostics = project.getProgram().compilerObject.getSyntacticDiagnostics(this.source);
        for (const diagnostic of diagnostics) {
            if (diagnostic.start === undefined) throw new SourceInvariantFailure('TypeScript syntax diagnostic has no source position.');
            const location = this.source.getLineAndCharacterOfPosition(diagnostic.start);
            throw new SourceParseFailure(filePath, location.line + 1, location.character + 1, ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n'));
        }
        this.digest = createHash('sha256').update(content).digest('hex');
        for (const family of ['declarations', 'functions', 'values', 'callable_values', 'anonymous_callables', 'namespaces', 'exports']) this.inventory[family] = this.coverage();
        this.inventory.unresolved_methods = this.coverage();
    }

    coverage(status: 'complete' | 'not_applicable' = 'complete'): Coverage { return { status, limitations: [] }; }
    limit(family: string, node: ts.Node, description: string): void {
        const coverage = this.inventory[family];
        coverage.status = 'incomplete';
        coverage.limitations.push({ kind: 'unsupported_syntax', location: { kind: 'source', start_line: this.line(node.getStart(this.source)), end_line: this.line(node.end - 1) }, description });
    }
    line(position: number): number { return this.source.getLineAndCharacterOfPosition(position).line + 1; }
    lineCount(node: ts.Node): number { return this.line(node.end - 1) - this.line(node.getStart(this.source)) + 1; }
    modifier(node: ts.Node, kind: ts.SyntaxKind): boolean { return ts.canHaveModifiers(node) && (ts.getModifiers(node)?.some(modifier => modifier.kind === kind) ?? false); }
    visibility(node: ts.Node): string { return this.modifier(node, ts.SyntaxKind.PrivateKeyword) ? 'private' : this.modifier(node, ts.SyntaxKind.ProtectedKeyword) ? 'protected' : 'public'; }
    decorators(node: ts.Node): string[] { return ts.canHaveDecorators(node) ? (ts.getDecorators(node)?.map(decorator => decorator.expression.getText(this.source)) ?? []) : []; }
    identity(node: ts.Node): Identity {
        const identity = this.identities.get(node);
        if (identity === undefined) throw new SourceInvariantFailure(`Missing indexed declaration at ${node.getStart(this.source)}.`);
        return identity;
    }
    container(node: ts.Node): ts.Node {
        const container = this.containers.get(node);
        if (container === undefined) throw new SourceInvariantFailure(`Missing native scope at ${node.getStart(this.source)}.`);
        return container;
    }
    aliasType(node: ts.TypeAliasDeclaration): ts.TypeNode {
        const type = this.aliasTypes.get(node);
        if (type === undefined) throw new SourceInvariantFailure(`Missing indexed alias type at ${node.getStart(this.source)}.`);
        return type;
    }
    createIdentity(node: ts.Node, family: Family, name: string, container: ts.Node): Identity {
        const parent = container === this.source ? undefined : this.identity(container);
        return { source_id: this.sourceId, content_digest: this.digest, family,
            qualified_name: parent === undefined ? name : `${parent.qualified_name}.${name}`, ordinal: node.getStart(this.source) + 1 };
    }
    callableNode(node: ts.Node): node is CallableNode {
        return ts.isFunctionDeclaration(node) || ts.isFunctionExpression(node) || ts.isArrowFunction(node) || ts.isMethodDeclaration(node)
            || ts.isMethodSignature(node) || ts.isConstructorDeclaration(node) || ts.isGetAccessorDeclaration(node) || ts.isSetAccessorDeclaration(node);
    }
    index(node: ts.Node, container: ts.Node): void {
        this.containers.set(node, container);
        let nested = container;
        if (ts.isClassDeclaration(node) || ts.isClassExpression(node) || ts.isInterfaceDeclaration(node) || ts.isTypeAliasDeclaration(node) || ts.isEnumDeclaration(node)) {
            const kind = ts.isInterfaceDeclaration(node) ? 'interface' : ts.isTypeAliasDeclaration(node) ? 'type_alias' : ts.isEnumDeclaration(node) ? 'enum' : this.modifier(node, ts.SyntaxKind.AbstractKeyword) ? 'abstract_class' : 'class';
            const family: Family = kind === 'type_alias' ? 'type' : kind === 'enum' ? 'class' : kind;
            const name = node.name === undefined ? `<anonymous>@${node.getStart(this.source)}` : node.name.getText(this.source);
            this.identities.set(node, this.createIdentity(node, family, name, container));
            this.declarationNodes.set(node, kind);
            if (ts.isTypeAliasDeclaration(node)) {
                let type = node.type;
                while (ts.isParenthesizedTypeNode(type)) type = type.type;
                this.aliasTypes.set(node, type);
            }
            nested = node;
        } else if (ts.isModuleDeclaration(node)) {
            this.identities.set(node, this.createIdentity(node, 'namespace', node.name.text, container));
            nested = node;
        } else if (this.callableNode(node)) {
            const parent = node.parent;
            const assigned = ts.isVariableDeclaration(parent) && ts.isIdentifier(parent.name);
            const method = ts.isMethodDeclaration(node) || ts.isMethodSignature(node) || ts.isGetAccessorDeclaration(node) || ts.isSetAccessorDeclaration(node);
            const kind: CallableKind = ts.isConstructorDeclaration(node) ? 'constructor' : method ? (this.modifier(node, ts.SyntaxKind.StaticKeyword) ? 'static_method' : 'instance_method')
                : ts.isFunctionDeclaration(node) ? 'function' : assigned ? 'callable_value' : 'anonymous';
            const name = ts.isConstructorDeclaration(node) ? 'constructor' : assigned ? parent.name.getText(this.source)
                : node.name === undefined ? `<anonymous>@${node.getStart(this.source)}` : node.name.getText(this.source);
            const family: Family = kind === 'function' ? 'function' : kind === 'callable_value' ? 'value' : kind === 'anonymous' ? 'callable' : 'method';
            this.identities.set(node, this.createIdentity(node, family, name, container));
            this.callableNodes.set(node, kind);
            nested = node;
        } else if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name)) {
            if (node.initializer === undefined || !this.callableNode(node.initializer)) this.identities.set(node, this.createIdentity(node, 'value', node.name.text, container));
        }
        ts.forEachChild(node, child => this.index(child, nested));
    }
    placement(node: ts.Node): Placement {
        const container = this.container(node);
        const identity = container === this.source ? undefined : this.identity(container);
        const enclosing: Container = identity === undefined ? { kind: 'file' } : { kind: 'declaration', declaration_id: identity };
        let scope: Scope = enclosing;
        for (let parent = node.parent; parent !== undefined && parent !== container; parent = parent.parent) {
            if (ts.isBlock(parent) && !ts.isModuleBlock(parent)) {
                scope = { kind: 'block', container: enclosing, start_utf8_offset: Buffer.byteLength(this.content.slice(0, parent.getStart(this.source))), end_utf8_offset: Buffer.byteLength(this.content.slice(0, parent.end)) };
                break;
            }
        }
        let namespace: Placement['namespace'] = { kind: 'none' };
        for (let parent: ts.Node = container; parent !== this.source; parent = this.container(parent)) {
            if (ts.isModuleDeclaration(parent)) {
                const identity = this.identity(parent);
                namespace = { kind: 'member', namespace_reference: identity.qualified_name, target: { kind: 'resolved', declaration_id: identity } };
                break;
            }
        }
        return { lexical_scope: scope, namespace };
    }
    type(node: ts.TypeNode | undefined): SourceType {
        if (node === undefined) return { kind: 'absent' };
        if (ts.isTypeReferenceNode(node)) return { kind: 'reference', name: node.typeName.getText(this.source), arguments: node.typeArguments?.map(type => this.type(type)) ?? [] };
        if ([ts.SyntaxKind.StringKeyword, ts.SyntaxKind.NumberKeyword, ts.SyntaxKind.BooleanKeyword, ts.SyntaxKind.VoidKeyword, ts.SyntaxKind.AnyKeyword, ts.SyntaxKind.UnknownKeyword, ts.SyntaxKind.NeverKeyword, ts.SyntaxKind.ObjectKeyword, ts.SyntaxKind.UndefinedKeyword, ts.SyntaxKind.BigIntKeyword, ts.SyntaxKind.SymbolKeyword].includes(node.kind))
            return { kind: 'reference', name: node.getText(this.source), arguments: [] };
        return { kind: 'unsupported' };
    }
    parameters(parameters: readonly ts.ParameterDeclaration[]): Parameter[] {
        return parameters.map(parameter => ({ name: parameter.name.getText(this.source), type: this.type(parameter.type), kind: parameter.dotDotDotToken === undefined ? 'positional' : 'variadic_positional', has_default: parameter.initializer !== undefined }));
    }
    bindingScope(node: ts.Node): ts.Node {
        let current = node.parent;
        if (this.callableNode(node) && (ts.isFunctionExpression(node) || ts.isArrowFunction(node)) && ts.isVariableDeclaration(current)) current = current.parent;
        const variable = ts.isVariableDeclaration(node) ? node :
            (ts.isFunctionExpression(node) || ts.isArrowFunction(node)) && ts.isVariableDeclaration(node.parent) ? node.parent : undefined;
        const hoisted = variable !== undefined && ts.isVariableDeclarationList(variable.parent) && (variable.parent.flags & ts.NodeFlags.BlockScoped) === 0;
        while (current !== this.source) {
            if (this.callableNode(current) || ts.isClassDeclaration(current) || ts.isClassExpression(current) || ts.isInterfaceDeclaration(current) || ts.isTypeAliasDeclaration(current) || ts.isModuleDeclaration(current)) return current;
            if (!hoisted && (ts.isBlock(current) || ts.isModuleBlock(current))) return current;
            current = current.parent;
        }
        return this.source;
    }
    bindings(reference: string, node: ts.Node): Identity[] {
        const parts = reference.split('.');
        let scope = this.bindingScope(node);
        const memberLookup = parts[0] === 'this';
        if (memberLookup) {
            for (let parent = node.parent; parent !== this.source; parent = parent.parent) {
                if (ts.isFunctionDeclaration(parent) || ts.isFunctionExpression(parent)) return [];
                if ((ts.isMethodDeclaration(parent) || ts.isGetAccessorDeclaration(parent) || ts.isSetAccessorDeclaration(parent)) && ts.isObjectLiteralExpression(parent.parent)) return [];
                if (ts.isClassDeclaration(parent) || ts.isClassExpression(parent)) break;
            }
            while (scope !== this.source && !ts.isClassDeclaration(scope) && !ts.isClassExpression(scope)) scope = this.bindingScope(scope);
            if (scope === this.source) return [];
            parts.shift();
        }
        let matches: ts.Node[] = [];
        while (true) {
            matches = [...this.identities].filter(([declaration, identity]) => this.bindingScope(declaration) === scope && (memberLookup || identity.family !== 'method') && identity.qualified_name.split('.').pop() === parts[0]).map(([declaration]) => declaration);
            if (matches.length || scope === this.source) break;
            if (this.callableNode(scope) && scope.parameters.some(parameter => parameter.name.getText(this.source) === parts[0])) return [];
            scope = this.bindingScope(scope);
        }
        for (const part of parts.slice(1)) {
            if (matches.length !== 1) return [];
            const parent = matches[0];
            matches = [...this.identities].filter(([declaration, identity]) => this.container(declaration) === parent && identity.qualified_name.split('.').pop() === part).map(([declaration]) => declaration);
        }
        return matches.map(node => this.identity(node));
    }
    resolve(reference: string, node: ts.Node): Target {
        const matches = this.bindings(reference, node);
        if (matches.length === 1) return { kind: 'resolved', declaration_id: matches[0] };
        return { kind: 'unresolved', reason: matches.length ? 'ambiguous' : 'unobserved' };
    }
    emitCallable(node: CallableNode, kind: CallableKind): Callable {
        const identity = this.identity(node);
        const name = ts.isConstructorDeclaration(node) ? 'constructor' : identity.qualified_name.split('.').pop();
        if (name === undefined) throw new SourceInvariantFailure('Callable identity has no name.');
        const fact: Callable = { declaration_id: identity, source_id: this.sourceId, name, qualified_name: identity.qualified_name, kind,
            visibility: this.visibility(node), visibility_intent: this.visibility(node), declaration_annotations: this.decorators(node),
            line_start: this.line(node.getStart(this.source)), line_end: this.line(node.end - 1), line_count: this.lineCount(node),
            parameters: this.parameters(node.parameters), return_type: this.type(node.type), decorators: this.decorators(node), docstring: '', placement: this.placement(node) };
        if (identity.family === 'method') {
            const container = this.container(node);
            const owner = this.identities.get(container);
            const directMember = node.parent === container || (ts.isTypeAliasDeclaration(container) && node.parent === this.aliasType(container));
            if (directMember && owner !== undefined && ['class', 'abstract_class', 'interface', 'type'].includes(owner.family)) fact.owner_declaration_id = owner;
            else { fact.owner = { kind: 'unresolved', reason: 'dynamic' }; fact.receiver_reference = node.parent.getText(this.source); }
        }
        if (kind === 'callable_value') { fact.declaration_kind = 'assignment'; fact.value_kind = 'value_callable'; fact.scope = this.container(node) === this.source ? 'module' : 'local'; }
        return fact;
    }
    emitProperty(node: ts.PropertyDeclaration | ts.PropertySignature | ts.GetAccessorDeclaration | ts.SetAccessorDeclaration | ts.ParameterDeclaration | ts.EnumMember, owner: Declaration): Property {
        const name = node.name.getText(this.source);
        const identity: Identity = { ...owner.declaration_id, family: 'property', qualified_name: `${owner.declaration_id.qualified_name}.${name}`, ordinal: node.getStart(this.source) + 1 };
        const type = ts.isEnumMember(node) ? undefined : ts.isSetAccessor(node) ? node.parameters[0]?.type : node.type;
        const optional = (ts.isPropertyDeclaration(node) || ts.isPropertySignature(node) || ts.isParameter(node)) && node.questionToken !== undefined;
        return { declaration_id: identity, owner_declaration_id: owner.declaration_id, name, type: this.type(type), is_optional: optional,
            visibility: this.visibility(node), member_kind: this.modifier(node, ts.SyntaxKind.StaticKeyword) || ts.isEnumMember(node) ? 'static' : 'instance', placement: this.placement(node),
            assigned_values: [{ kind: 'unsupported', expression: '', reference: '' }] };
    }
    emitDeclaration(node: DeclarationNode, kind: string): Declaration {
        const identity = this.identity(node);
        const fact: Declaration = { declaration_id: identity, kind, name: node.name?.getText(this.source) ?? identity.qualified_name,
            visibility: 'public', visibility_intent: 'public', declaration_annotations: this.decorators(node), line_count: this.lineCount(node),
            methods: [], abstract_methods: [], properties: [], signatures: [], placement: this.placement(node), inventory: { methods: this.coverage(), abstract_methods: this.coverage(), properties: this.coverage(), signatures: this.coverage() } };
        let members: readonly ts.Node[];
        if (ts.isTypeAliasDeclaration(node)) {
            const type = this.aliasType(node);
            members = ts.isTypeLiteralNode(type) ? type.members : [];
            if (ts.isFunctionTypeNode(type) || ts.isConstructorTypeNode(type)) fact.signatures.push(this.emitSignature(type, ts.isFunctionTypeNode(type) ? 'call' : 'construct'));
        } else members = node.members;
        for (const member of members) {
            const callable = this.callables.get(member);
            if (callable !== undefined) {
                if (ts.isMethodSignature(member) || this.modifier(member, ts.SyntaxKind.AbstractKeyword)) fact.abstract_methods.push(callable);
                else fact.methods.push(callable);
            }
            if (ts.isPropertyDeclaration(member) || ts.isPropertySignature(member) || ts.isGetAccessorDeclaration(member) || ts.isSetAccessorDeclaration(member) || ts.isEnumMember(member)) {
                if (!fact.properties.some(property => property.name === member.name.getText(this.source))) fact.properties.push(this.emitProperty(member, fact));
            }
            if (ts.isConstructorDeclaration(member)) for (const parameter of member.parameters) {
                if ([ts.SyntaxKind.PublicKeyword, ts.SyntaxKind.ProtectedKeyword, ts.SyntaxKind.PrivateKeyword, ts.SyntaxKind.ReadonlyKeyword].some(kind => this.modifier(parameter, kind))) fact.properties.push(this.emitProperty(parameter, fact));
            }
            if (ts.isCallSignatureDeclaration(member) || ts.isConstructSignatureDeclaration(member) || ts.isIndexSignatureDeclaration(member)) fact.signatures.push(this.emitSignature(member, ts.isCallSignatureDeclaration(member) ? 'call' : ts.isConstructSignatureDeclaration(member) ? 'construct' : 'index'));
        }
        if (ts.isClassDeclaration(node) || ts.isClassExpression(node) || ts.isInterfaceDeclaration(node)) for (const clause of node.heritageClauses ?? []) for (const type of clause.types) {
            const reference = type.expression.getText(this.source);
            this.relations.push({ source_declaration_id: identity, kind: clause.token === ts.SyntaxKind.ExtendsKeyword ? 'extends' : 'implements', target_reference: reference, target: this.resolve(reference, node) });
        }
        return fact;
    }
    emitSignature(node: ts.SignatureDeclaration, kind: Signature['kind']): Signature {
        return { kind, line_count: this.lineCount(node), declared_args: node.parameters.length,
            optional_args: node.parameters.filter(parameter => parameter.questionToken !== undefined || parameter.initializer !== undefined).length };
    }
    normalized(specifier: string): string {
        return specifier.startsWith('.') ? path.relative(this.root, path.resolve(path.dirname(this.filePath), specifier)).split(path.sep).join('/').replace(/\.[^/.]+$/, '') : specifier;
    }
    export(name: string, local: string, node: ts.Node, specifier = '', isDefault = false): void {
        const reexport = specifier !== '';
        const references = this.bindings(local, node);
        const own = this.identities.get(node);
        const binding: Export['binding'] = reexport ? { kind: 'unresolved', reason: 'external' } : own !== undefined ? { kind: 'resolved', declaration_ids: [own] }
            : references.length ? { kind: 'resolved', declaration_ids: references } : { kind: 'unresolved', reason: 'unobserved' };
        const family = binding.kind === 'resolved' ? binding.declaration_ids[0].family : 'unknown';
        this.exports.push({ name, local_name: local, kind: family === 'namespace' ? 'module' : family === 'callable' || family === 'method' || family === 'property' ? 'unknown' : family,
            crossing_type: 'symbol', path: specifier, is_relative: specifier.startsWith('.'), normalized_path: this.normalized(specifier), is_reexport: reexport, is_default: isDefault, is_aliased: name !== local, statement_id: node.getStart(this.source) + 1, binding });
    }
    importedSymbol(name: string, alias: string, isDefault: boolean, isNamespace: boolean, isStar: boolean): Import['imported_symbols'][number] {
        return { name, alias, is_aliased: name !== alias, is_default: isDefault, is_namespace: isNamespace, is_star: isStar };
    }
    addImport(specifier: string, symbols: Import['imported_symbols'], node: ts.Node): void {
        const module = symbols.length === 0;
        if (module) symbols.push(this.importedSymbol('*', '*', false, false, true));
        const normalized = this.normalized(specifier);
        this.imports.push({ path: specifier, is_relative: specifier.startsWith('.'), normalized_path: normalized,
            imported_name: symbols[0].alias, is_aliased: symbols.some(symbol => symbol.is_aliased), crossing_type: module ? 'module' : 'symbol',
            file_barrier_crossed: true, statement_id: node.getStart(this.source) + 1, join_key: normalized, uses_joined_import: symbols.length > 1, imported_symbols: symbols });
    }
    observe(node: ts.Node): void {
        if (ts.isModuleDeclaration(node)) this.namespaces.push({ kind: ts.isStringLiteral(node.name) ? 'module' : 'namespace', declaration_id: this.identity(node), placement: this.placement(node) });
        if (ts.isImportDeclaration(node)) {
            if (!ts.isStringLiteral(node.moduleSpecifier)) throw new SourceInvariantFailure('Import module specifier is not a string literal.');
            const specifier = node.moduleSpecifier.text;
            const symbols: Import['imported_symbols'] = [];
            const clause = node.importClause;
            if (clause?.name !== undefined) symbols.push(this.importedSymbol('default', clause.name.text, true, false, false));
            const bindings = clause?.namedBindings;
            if (bindings !== undefined) {
                if (ts.isNamespaceImport(bindings)) symbols.push(this.importedSymbol('*', bindings.name.text, false, true, true));
                else for (const item of bindings.elements) symbols.push(this.importedSymbol(item.propertyName?.text ?? item.name.text, item.name.text, false, false, false));
            }
            this.addImport(specifier, symbols, node);
        }
        if (ts.isCallExpression(node) && (node.expression.kind === ts.SyntaxKind.ImportKeyword || (ts.isIdentifier(node.expression) && node.expression.text === 'require'))) {
            const specifier = node.arguments[0];
            if (specifier !== undefined && ts.isStringLiteral(specifier)) this.addImport(specifier.text, [], node);
        }
        if (ts.isVariableDeclaration(node)) {
            if (!ts.isIdentifier(node.name)) {
                this.limit('values', node, 'Destructured value bindings are not represented.');
                this.limit('callable_values', node, 'Destructured bindings cannot be tied to an exact callable value.');
            }
            else if (this.identities.has(node)) {
                const constant = ts.isVariableDeclarationList(node.parent) && (node.parent.flags & ts.NodeFlags.Const) !== 0;
                const value: Value = { declaration_id: this.identity(node), name: node.name.text, visibility: 'public', visibility_intent: 'public', line_count: this.lineCount(node), declaration_kind: constant ? 'constant' : 'assignment',
                    value_kind: node.initializer === undefined ? 'value_unknown' : ts.isClassExpression(node.initializer) ? 'value_class' : ts.isObjectLiteralExpression(node.initializer) ? 'value_object' : ts.isLiteralExpression(node.initializer) ? 'value_literal' : 'value_unknown',
                    scope: this.container(node) === this.source ? 'module' : 'local', placement: this.placement(node) };
                this.values.push(value);
            }
        }
        if (this.modifier(node, ts.SyntaxKind.ExportKeyword) && this.identities.has(node)) {
            const identity = this.identity(node); const name = identity.qualified_name.split('.').pop();
            if (name === undefined) throw new SourceInvariantFailure('Export has no native name.');
            this.export(this.modifier(node, ts.SyntaxKind.DefaultKeyword) ? 'default' : name, name, node, '', this.modifier(node, ts.SyntaxKind.DefaultKeyword));
        }
        if (ts.isVariableStatement(node) && this.modifier(node, ts.SyntaxKind.ExportKeyword)) for (const declaration of node.declarationList.declarations) {
            if (ts.isIdentifier(declaration.name)) {
                const binding = declaration.initializer !== undefined && this.callableNode(declaration.initializer) ? declaration.initializer : declaration;
                this.export(declaration.name.text, declaration.name.text, binding);
            }
        }
        if (ts.isExportDeclaration(node)) {
            const specifier = node.moduleSpecifier;
            if (specifier !== undefined && !ts.isStringLiteral(specifier)) throw new SourceInvariantFailure('Export module specifier is not a string literal.');
            const module = specifier?.text ?? '';
            if (node.exportClause === undefined) { this.export('*', '*', node, module); this.limit('exports', node, 'Wildcard export bindings require the external module inventory.'); }
            else if (ts.isNamespaceExport(node.exportClause)) this.export(node.exportClause.name.text, '*', node, module);
            else for (const element of node.exportClause.elements) this.export(element.name.text, element.propertyName?.text ?? element.name.text, node, module);
        }
        if (ts.isExportAssignment(node)) this.export('default', node.expression.getText(this.source), node, '', true);
        ts.forEachChild(node, child => this.observe(child));
    }
    calls(): Call[] {
        const result: Call[] = []; const ordinals = new Map<ts.Node, number>();
        const visit = (node: ts.Node): void => {
            if (ts.isCallExpression(node) || ts.isNewExpression(node)) {
                let owner = this.container(node);
                while (owner !== this.source && !this.callables.has(owner)) owner = this.container(owner);
                const source = this.callables.get(owner);
                if (source !== undefined) {
                    const expression = node.expression.getText(this.source);
                    const target = this.resolve(expression, node);
                    let candidates = target.kind === 'resolved' ? [...this.callables.values()].filter(callable => callable.declaration_id === target.declaration_id) : [];
                    if (ts.isNewExpression(node) && target.kind === 'resolved') candidates = [...this.callables.values()].filter(callable => callable.kind === 'constructor' && callable.owner_declaration_id === target.declaration_id);
                    const ordinal = (ordinals.get(owner) ?? 0) + 1; ordinals.set(owner, ordinal);
                    result.push({ source_callable_id: source.declaration_id, ordinal, target_callable_id: candidates.length === 1 ? candidates[0].declaration_id : null,
                        source_id: this.sourceId, line: this.line(node.getStart(this.source)), expression, resolution: candidates.length === 1 ? 'resolved' : ts.isIdentifier(node.expression) || ts.isPropertyAccessExpression(node.expression) ? 'unresolved' : 'dynamic', target_name: expression.split('.').pop() ?? expression });
                }
            }
            ts.forEachChild(node, visit);
        }; visit(this.source); return result;
    }
    extract(): ExtractedFile {
        this.index(this.source, this.source);
        for (const [node, kind] of this.callableNodes) this.callables.set(node, this.emitCallable(node, kind));
        for (const [node, kind] of this.declarationNodes) this.declarations.set(node, this.emitDeclaration(node, kind));
        this.observe(this.source);
        const callables = [...this.callables.values()];
        return { imports: this.imports, exports: this.exports, namespaces: this.namespaces, declarations: [...this.declarations.values()], functions: callables.filter(callable => callable.kind === 'function'), values: this.values,
            callable_values: callables.filter(callable => callable.kind === 'callable_value'), anonymous_callables: callables.filter(callable => callable.kind === 'anonymous'), unresolved_methods: callables.filter(callable => callable.owner !== undefined), calls: this.calls(), declaration_relations: this.relations, inventory: this.inventory,
            line_count: this.content.split('\n').length, code_line_count: this.content.split('\n').filter(line => line.trim() !== '' && !line.trim().startsWith('//')).length, public_symbol_count: new Set(this.exports.filter(item => !item.is_reexport).map(item => item.name)).size };
    }
}

class Script {
    readInput(): Map<string, string> {
        const document: unknown = JSON.parse(fs.readFileSync(0, 'utf8'));
        if (document === null || typeof document !== 'object' || Array.isArray(document)) throw new InputContractFailure('Expected a source-id to path object.');
        const inputs = new Map<string, string>();
        for (const [id, file] of Object.entries(document)) {
            if (typeof file !== 'string') throw new InputContractFailure('Source paths must be strings.');
            inputs.set(id, file);
        }
        return inputs;
    }
    run(): void {
        const batch = process.argv[2] === '--batch';
        const root = path.resolve(process.argv[3] ?? process.cwd());
        const file = process.argv[2];
        if (file === undefined) throw new InputContractFailure('Expected a source path or --batch.');
        const inputs = batch ? this.readInput() : new Map([[path.relative(root, path.resolve(file)).replace(/\.[^/.]+$/, ''), file]]);
        const output: Record<string, ExtractedFile> = {};
        for (const [id, file] of inputs) {
            const result = new TypeScriptExtractor(id, path.resolve(file), root, fs.readFileSync(file, 'utf8')).extract();
            if (batch && process.argv.includes('--jsonl')) console.log(JSON.stringify([id, result]));
            else output[id] = result;
        }
        if (!batch) console.log(JSON.stringify(Object.values(output)[0]));
        else if (!process.argv.includes('--jsonl')) console.log(JSON.stringify(output));
    }
}
try { new Script().run(); } catch (error) {
    if (error instanceof SourceParseFailure) { console.error(`modwire-error:${JSON.stringify({ code: 'source_parse', language: 'typescript', path: error.sourcePath, line: error.line, column: error.column, diagnostic: error.diagnostic })}`); process.exitCode = 1; }
    else throw error;
}
