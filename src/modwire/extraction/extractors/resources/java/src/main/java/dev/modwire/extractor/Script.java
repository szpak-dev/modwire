package dev.modwire.extractor;

import com.github.javaparser.ParserConfiguration;
import com.github.javaparser.ParseProblemException;
import com.github.javaparser.Problem;
import com.github.javaparser.Range;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.body.AnnotationDeclaration;
import com.github.javaparser.ast.body.AnnotationMemberDeclaration;
import com.github.javaparser.ast.body.BodyDeclaration;
import com.github.javaparser.ast.body.CallableDeclaration;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.CompactConstructorDeclaration;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.EnumConstantDeclaration;
import com.github.javaparser.ast.body.EnumDeclaration;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.Parameter;
import com.github.javaparser.ast.body.RecordDeclaration;
import com.github.javaparser.ast.body.TypeDeclaration;
import com.github.javaparser.ast.body.VariableDeclarator;
import com.github.javaparser.ast.expr.AnnotationExpr;
import com.github.javaparser.ast.expr.MethodCallExpr;
import com.github.javaparser.ast.expr.ObjectCreationExpr;
import com.github.javaparser.ast.nodeTypes.NodeWithModifiers;
import com.github.javaparser.ast.type.ClassOrInterfaceType;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public final class Script {
    private final Gson gson = new GsonBuilder().serializeNulls().create();

    public static void main(String[] arguments) {
        try {
            new Script().run(arguments);
        } catch (SourceParseFailure error) {
            System.err.println("modwire-error:" + new Gson().toJson(error.document()));
            System.exit(1);
        } catch (Exception error) {
            System.err.println(error.getMessage());
            System.exit(1);
        }
    }

    private void run(String[] arguments) throws IOException {
        if (arguments.length < 2 || !"--batch".equals(arguments[0])) {
            throw new IllegalArgumentException("Expected --batch followed by the Java source root.");
        }
        StaticJavaParser.setConfiguration(
            new ParserConfiguration().setLanguageLevel(ParserConfiguration.LanguageLevel.JAVA_25)
        );
        JsonElement input = JsonParser.parseReader(
            new java.io.InputStreamReader(System.in, StandardCharsets.UTF_8)
        );
        if (!input.isJsonObject()) {
            throw new IllegalArgumentException("Expected a JSON object mapping source ids to Java file paths.");
        }
        boolean jsonLines = false;
        for (String argument : arguments) {
            if ("--jsonl".equals(argument)) {
                jsonLines = true;
            }
        }
        JavaSourceExtractor extractor = new JavaSourceExtractor();
        JsonObject result = new JsonObject();
        for (Map.Entry<String, JsonElement> entry : input.getAsJsonObject().entrySet()) {
            if (!entry.getValue().isJsonPrimitive() || !entry.getValue().getAsJsonPrimitive().isString()) {
                throw new IllegalArgumentException("Expected source ids and paths to be strings.");
            }
            JsonObject extracted = extractor.extract(Path.of(entry.getValue().getAsString()), entry.getKey());
            if (jsonLines) {
                JsonArray line = new JsonArray();
                line.add(entry.getKey());
                line.add(extracted);
                System.out.println(gson.toJson(line));
            } else {
                result.add(entry.getKey(), extracted);
            }
        }
        if (!jsonLines) {
            System.out.println(gson.toJson(result));
        }
    }
}

final class JavaSourceExtractor {
    private final List<CallableFact> callableFacts = new ArrayList<>();
    private final Map<String, List<CallableFact>> callablesByName = new HashMap<>();
    private final Map<String, List<CallableFact>> callablesByQualifiedName = new HashMap<>();
    private final Map<String, List<CallableFact>> constructorsByOwner = new HashMap<>();
    private String sourceId = "";

    JsonObject extract(Path path, String sourceIdentity) throws IOException {
        sourceId = sourceIdentity;
        callableFacts.clear();
        callablesByName.clear();
        callablesByQualifiedName.clear();
        constructorsByOwner.clear();

        String content = Files.readString(path, StandardCharsets.UTF_8);
        CompilationUnit unit;
        try {
            unit = StaticJavaParser.parse(content);
        } catch (ParseProblemException error) {
            Problem problem = error.getProblems().get(0);
            Range location = problem.getLocation()
                .flatMap(tokenRange -> tokenRange.getBegin().getRange())
                .orElseThrow(() -> new ExtractorInvariantFailure(
                    "Java parser omitted the source parse location for " + path + ".",
                    error
                ));
            throw new SourceParseFailure(
                path.toString(),
                location.begin.line,
                location.begin.column,
                problem.getMessage(),
                error
            );
        }
        JsonArray declarations = new JsonArray();
        JsonArray callables = new JsonArray();
        JsonArray relations = new JsonArray();
        JsonArray namespaces = namespaces(unit);

        for (TypeDeclaration<?> declaration : unit.getTypes()) {
            collectType(declaration, "", declarations, callables, relations);
        }
        indexCallables();

        JsonObject result = new JsonObject();
        result.add("imports", imports(unit));
        result.add("exports", new JsonArray());
        result.add("namespaces", namespaces);
        result.add("declarations", declarations);
        result.add("functions", new JsonArray());
        result.add("values", new JsonArray());
        result.add("callable_values", new JsonArray());
        result.add("anonymous_callables", new JsonArray());
        result.add("calls", calls());
        result.add("declaration_relations", relations);
        result.addProperty("line_count", content.split("\\R", -1).length);
        result.addProperty("code_line_count", codeLineCount(content));
        result.addProperty("public_symbol_count", publicSymbolCount(declarations));
        return result;
    }

    private JsonArray namespaces(CompilationUnit unit) {
        JsonArray namespaces = new JsonArray();
        unit.getPackageDeclaration().ifPresent(declaration -> {
            JsonObject namespace = new JsonObject();
            namespace.addProperty("kind", "package");
            namespace.addProperty("qualified_name", declaration.getNameAsString());
            namespaces.add(namespace);
        });
        return namespaces;
    }

    private JsonArray imports(CompilationUnit unit) {
        JsonArray imports = new JsonArray();
        int statementId = 0;
        for (ImportDeclaration declaration : unit.getImports()) {
            statementId += 1;
            String imported = declaration.getNameAsString();
            String path = imported + (declaration.isAsterisk() ? ".*" : "");
            String importedName = declaration.isAsterisk() ? "*" : lastPart(imported);
            String normalized = imported.replace('.', '/');
            if (declaration.isStatic() && !declaration.isAsterisk()) {
                normalized = parentPath(normalized);
            }
            if (declaration.isAsterisk()) {
                normalized = normalized + "/*";
            }
            JsonObject symbol = new JsonObject();
            symbol.addProperty("name", importedName);
            symbol.addProperty("alias", importedName);
            symbol.addProperty("is_aliased", false);
            symbol.addProperty("is_default", false);
            symbol.addProperty("is_namespace", false);
            symbol.addProperty("is_star", declaration.isAsterisk());
            JsonArray symbols = new JsonArray();
            symbols.add(symbol);

            JsonObject fact = new JsonObject();
            fact.addProperty("path", path);
            fact.addProperty("is_relative", false);
            fact.addProperty("normalized_path", normalized);
            fact.addProperty("imported_name", importedName);
            fact.addProperty("is_aliased", false);
            fact.addProperty("crossing_type", declaration.isAsterisk() ? "module" : "symbol");
            fact.addProperty("file_barrier_crossed", true);
            fact.addProperty("statement_id", statementId);
            fact.addProperty("join_key", normalized);
            fact.addProperty("uses_joined_import", false);
            fact.add("imported_symbols", symbols);
            imports.add(fact);
        }
        return imports;
    }

    private void collectType(
        TypeDeclaration<?> declaration,
        String owner,
        JsonArray declarations,
        JsonArray callables,
        JsonArray relations
    ) {
        String qualifiedName = owner.isEmpty()
            ? declaration.getNameAsString()
            : owner + "." + declaration.getNameAsString();
        DeclarationKind kind = declarationKind(declaration);
        JsonObject identity = declarationIdentity(kind.family(), qualifiedName, ordinal(declaration));
        String visibility = visibility(declaration, implicitTypeVisibility(declaration));
        JsonArray methods = new JsonArray();
        JsonArray abstractMethods = new JsonArray();
        JsonArray properties = new JsonArray();

        collectProperties(declaration, identity, properties);
        collectCallableDeclarations(declaration, identity, qualifiedName, methods, abstractMethods, callables);

        JsonObject fact = new JsonObject();
        fact.add("declaration_id", identity.deepCopy());
        fact.addProperty("kind", kind.kind());
        fact.addProperty("name", qualifiedName);
        fact.addProperty("visibility", visibility);
        fact.addProperty("visibility_intent", visibility);
        fact.add("declaration_annotations", annotations(declaration.getAnnotations()));
        fact.addProperty("line_count", lineCount(declaration));
        fact.add("methods", methods);
        fact.add("abstract_methods", abstractMethods);
        fact.add("properties", properties);
        fact.add("signatures", new JsonArray());
        declarations.add(fact);

        collectRelations(declaration, identity, relations);
        for (BodyDeclaration<?> member : declaration.getMembers()) {
            if (member.isTypeDeclaration()) {
                collectType(member.asTypeDeclaration(), qualifiedName, declarations, callables, relations);
            }
        }
    }

    private void collectProperties(TypeDeclaration<?> declaration, JsonObject ownerIdentity, JsonArray properties) {
        boolean implicitStaticFields = (
            declaration.isClassOrInterfaceDeclaration()
                && declaration.asClassOrInterfaceDeclaration().isInterface()
        ) || declaration.isAnnotationDeclaration();
        for (FieldDeclaration field : declaration.getFields()) {
            String fallback = implicitStaticFields ? "public" : "internal";
            for (VariableDeclarator variable : field.getVariables()) {
                properties.add(property(
                    variable,
                    ownerIdentity,
                    variable.getNameAsString(),
                    variable.getType().toString(),
                    visibility(field, fallback),
                    field.isStatic() || implicitStaticFields ? "static" : "instance"
                ));
            }
        }
        if (declaration.isRecordDeclaration()) {
            for (Parameter component : declaration.asRecordDeclaration().getParameters()) {
                properties.add(property(
                    component,
                    ownerIdentity,
                    component.getNameAsString(),
                    component.getType().toString(),
                    "public",
                    "instance"
                ));
            }
        }
        if (declaration.isEnumDeclaration()) {
            for (EnumConstantDeclaration entry : declaration.asEnumDeclaration().getEntries()) {
                properties.add(property(
                    entry,
                    ownerIdentity,
                    entry.getNameAsString(),
                    declaration.getNameAsString(),
                    "public",
                    "static"
                ));
            }
        }
        if (declaration.isAnnotationDeclaration()) {
            for (BodyDeclaration<?> member : declaration.getMembers()) {
                if (member.isAnnotationMemberDeclaration()) {
                    AnnotationMemberDeclaration annotationMember = member.asAnnotationMemberDeclaration();
                    properties.add(property(
                        annotationMember,
                        ownerIdentity,
                        annotationMember.getNameAsString(),
                        annotationMember.getType().toString(),
                        "public",
                        "instance"
                    ));
                }
            }
        }
    }

    private JsonObject property(
        Node declaration,
        JsonObject ownerIdentity,
        String name,
        String annotation,
        String visibility,
        String memberKind
    ) {
        JsonObject value = new JsonObject();
        value.addProperty("kind", "unsupported");
        value.addProperty("expression", "");
        value.addProperty("reference", "");
        JsonArray assignedValues = new JsonArray();
        assignedValues.add(value);

        JsonObject property = new JsonObject();
        property.add(
            "declaration_id",
            declarationIdentity(
                "property",
                ownerIdentity.get("qualified_name").getAsString() + "." + name,
                ordinal(declaration)
            )
        );
        property.add("owner_declaration_id", ownerIdentity.deepCopy());
        property.addProperty("name", name);
        property.addProperty("is_optional", false);
        property.add("type", sourceType(annotation));
        property.addProperty("visibility", visibility);
        property.addProperty("member_kind", memberKind);
        property.add("assigned_values", assignedValues);
        return property;
    }

    private void collectCallableDeclarations(
        TypeDeclaration<?> declaration,
        JsonObject ownerIdentity,
        String owner,
        JsonArray methods,
        JsonArray abstractMethods,
        JsonArray callables
    ) {
        boolean interfaceDeclaration = declaration.isClassOrInterfaceDeclaration()
            && declaration.asClassOrInterfaceDeclaration().isInterface();
        String methodFallback = interfaceDeclaration ? "public" : "internal";
        String constructorFallback = declaration.isEnumDeclaration() ? "private" : methodFallback;
        for (ConstructorDeclaration constructor : declaration.getConstructors()) {
            JsonObject callable = addCallable(
                constructor,
                "constructor",
                ownerIdentity,
                owner,
                "constructor",
                "",
                visibility(constructor, constructorFallback),
                callables
            );
            methods.add(callable.deepCopy());
        }
        if (declaration.isRecordDeclaration()) {
            RecordDeclaration record = declaration.asRecordDeclaration();
            for (CompactConstructorDeclaration constructor : record.getCompactConstructors()) {
                String constructorVisibility = visibility(
                    constructor,
                    visibility(record, implicitTypeVisibility(record))
                );
                JsonObject callable = addCompactConstructor(
                    constructor,
                    record.getParameters(),
                    ownerIdentity,
                    owner,
                    constructorVisibility,
                    callables
                );
                methods.add(callable.deepCopy());
            }
        }
        for (MethodDeclaration method : declaration.getMethods()) {
            String methodVisibility = visibility(method, methodFallback);
            JsonObject callable = addCallable(
                method,
                method.getNameAsString(),
                ownerIdentity,
                owner,
                method.isStatic() ? "static_method" : "instance_method",
                method.getType().toString(),
                methodVisibility,
                callables
            );
            if (!interfaceDeclaration && (method.isAbstract() || method.getBody().isEmpty())) {
                abstractMethods.add(callable.deepCopy());
            } else {
                methods.add(callable.deepCopy());
            }
        }
        if (declaration.isAnnotationDeclaration()) {
            for (BodyDeclaration<?> member : declaration.getMembers()) {
                if (member.isAnnotationMemberDeclaration()) {
                    AnnotationMemberDeclaration annotationMember = member.asAnnotationMemberDeclaration();
                    JsonObject callable = addAnnotationCallable(
                        annotationMember,
                        ownerIdentity,
                        owner,
                        callables
                    );
                    abstractMethods.add(callable.deepCopy());
                }
            }
        }
    }

    private JsonObject addCallable(
        CallableDeclaration<?> declaration,
        String name,
        JsonObject ownerIdentity,
        String owner,
        String kind,
        String returnAnnotation,
        String visibility,
        JsonArray callables
    ) {
        String qualifiedName = owner + "." + name;
        int ordinal = ordinal(declaration);
        JsonObject callable = callable(
            declaration,
            declaration.getParameters(),
            name,
            ownerIdentity,
            owner,
            qualifiedName,
            kind,
            returnAnnotation,
            visibility,
            ordinal
        );
        callables.add(callable);
        callableFacts.add(new CallableFact(declaration, callable, name, owner, qualifiedName, "constructor".equals(kind)));
        return callable;
    }

    private JsonObject addAnnotationCallable(
        AnnotationMemberDeclaration declaration,
        JsonObject ownerIdentity,
        String owner,
        JsonArray callables
    ) {
        String name = declaration.getNameAsString();
        String qualifiedName = owner + "." + name;
        int ordinal = ordinal(declaration);
        JsonObject callable = callable(
            declaration,
            List.of(),
            name,
            ownerIdentity,
            owner,
            qualifiedName,
            "instance_method",
            declaration.getType().toString(),
            "public",
            ordinal
        );
        callables.add(callable);
        callableFacts.add(new CallableFact(declaration, callable, name, owner, qualifiedName, false));
        return callable;
    }

    private JsonObject addCompactConstructor(
        CompactConstructorDeclaration declaration,
        List<Parameter> parameters,
        JsonObject ownerIdentity,
        String owner,
        String visibility,
        JsonArray callables
    ) {
        String qualifiedName = owner + ".constructor";
        int ordinal = ordinal(declaration);
        JsonObject callable = callable(
            declaration,
            parameters,
            "constructor",
            ownerIdentity,
            owner,
            qualifiedName,
            "constructor",
            "",
            visibility,
            ordinal
        );
        callables.add(callable);
        callableFacts.add(new CallableFact(declaration, callable, "constructor", owner, qualifiedName, true));
        return callable;
    }

    private JsonObject callable(
        Node declaration,
        List<Parameter> parameters,
        String name,
        JsonObject ownerIdentity,
        String owner,
        String qualifiedName,
        String kind,
        String returnAnnotation,
        String visibility,
        int ordinal
    ) {
        JsonObject callable = new JsonObject();
        callable.add("declaration_id", declarationIdentity("method", qualifiedName, ordinal));
        callable.addProperty("source_id", sourceId);
        callable.addProperty("name", name);
        callable.addProperty("qualified_name", qualifiedName);
        callable.addProperty("kind", kind);
        callable.addProperty("visibility", visibility);
        callable.addProperty("visibility_intent", visibility);
        callable.add("declaration_annotations", annotationsForNode(declaration));
        callable.addProperty("line_start", beginLine(declaration));
        callable.addProperty("line_end", endLine(declaration));
        callable.addProperty("line_count", lineCount(declaration));
        callable.add("parameters", parameters(parameters));
        callable.add("return_type", sourceType(returnAnnotation));
        callable.add("decorators", annotationsForNode(declaration));
        callable.addProperty("docstring", "");
        callable.add("owner_declaration_id", ownerIdentity.deepCopy());
        return callable;
    }

    private JsonArray parameters(List<Parameter> parameters) {
        JsonArray result = new JsonArray();
        for (Parameter parameter : parameters) {
            JsonObject fact = new JsonObject();
            fact.addProperty("name", parameter.getNameAsString());
            fact.add("type", sourceType(parameter.getType().toString()));
            fact.addProperty("kind", parameter.isVarArgs() ? "variadic_positional" : "positional");
            fact.addProperty("has_default", false);
            result.add(fact);
        }
        return result;
    }

    private JsonObject sourceType(String authoredType) {
        String value = authoredType.strip();
        JsonObject type = new JsonObject();
        if (value.isEmpty()) {
            type.addProperty("kind", "absent");
            return type;
        }
        if (value.contains("?") || value.contains("[") || value.contains("&") || value.contains("|")) {
            type.addProperty("kind", "unsupported");
            return type;
        }
        int genericStart = value.indexOf('<');
        if (genericStart < 0) {
            type.addProperty("kind", "reference");
            type.addProperty("name", value);
            type.add("arguments", new JsonArray());
            return type;
        }
        if (!value.endsWith(">")) {
            type.addProperty("kind", "unsupported");
            return type;
        }
        String name = value.substring(0, genericStart).strip();
        List<String> arguments = genericArguments(value.substring(genericStart + 1, value.length() - 1));
        if (name.isEmpty() || arguments.isEmpty()) {
            type.addProperty("kind", "unsupported");
            return type;
        }
        JsonArray typeArguments = new JsonArray();
        for (String argument : arguments) {
            typeArguments.add(sourceType(argument));
        }
        type.addProperty("kind", "reference");
        type.addProperty("name", name);
        type.add("arguments", typeArguments);
        return type;
    }

    private List<String> genericArguments(String content) {
        List<String> arguments = new ArrayList<>();
        int depth = 0;
        int start = 0;
        for (int index = 0; index < content.length(); index++) {
            char token = content.charAt(index);
            if (token == '<') {
                depth++;
            } else if (token == '>') {
                depth--;
            } else if (token == ',' && depth == 0) {
                arguments.add(content.substring(start, index).strip());
                start = index + 1;
            }
        }
        if (depth != 0) {
            return List.of();
        }
        arguments.add(content.substring(start).strip());
        return arguments.stream().filter(argument -> !argument.isEmpty()).toList();
    }

    private void collectRelations(TypeDeclaration<?> declaration, JsonObject identity, JsonArray relations) {
        if (declaration.isClassOrInterfaceDeclaration()) {
            ClassOrInterfaceDeclaration typed = declaration.asClassOrInterfaceDeclaration();
            for (ClassOrInterfaceType target : typed.getExtendedTypes()) {
                relations.add(relation(identity, "extends", target.toString()));
            }
            for (ClassOrInterfaceType target : typed.getImplementedTypes()) {
                relations.add(relation(identity, "implements", target.toString()));
            }
        } else if (declaration.isRecordDeclaration()) {
            RecordDeclaration typed = declaration.asRecordDeclaration();
            for (ClassOrInterfaceType target : typed.getImplementedTypes()) {
                relations.add(relation(identity, "implements", target.toString()));
            }
        } else if (declaration.isEnumDeclaration()) {
            EnumDeclaration typed = declaration.asEnumDeclaration();
            for (ClassOrInterfaceType target : typed.getImplementedTypes()) {
                relations.add(relation(identity, "implements", target.toString()));
            }
        }
    }

    private JsonObject relation(JsonObject identity, String kind, String target) {
        JsonObject relation = new JsonObject();
        relation.add("source_declaration_id", identity.deepCopy());
        relation.addProperty("kind", kind);
        relation.addProperty("target_reference", target);
        return relation;
    }

    private void indexCallables() {
        for (CallableFact fact : callableFacts) {
            callablesByName.computeIfAbsent(fact.name(), ignored -> new ArrayList<>()).add(fact);
            callablesByQualifiedName.computeIfAbsent(fact.qualifiedName(), ignored -> new ArrayList<>()).add(fact);
            if (fact.constructor()) {
                constructorsByOwner.computeIfAbsent(fact.owner(), ignored -> new ArrayList<>()).add(fact);
                constructorsByOwner.computeIfAbsent(lastPart(fact.owner()), ignored -> new ArrayList<>()).add(fact);
            }
        }
    }

    private JsonArray calls() {
        JsonArray calls = new JsonArray();
        for (CallableFact source : callableFacts) {
            List<Node> expressions = new ArrayList<>();
            for (MethodCallExpr expression : source.node().findAll(MethodCallExpr.class)) {
                if (belongsTo(expression, source.node())) {
                    expressions.add(expression);
                }
            }
            for (ObjectCreationExpr expression : source.node().findAll(ObjectCreationExpr.class)) {
                if (belongsTo(expression, source.node())) {
                    expressions.add(expression);
                }
            }
            expressions.sort((left, right) -> {
                int start = left.getBegin().orElseThrow().compareTo(right.getBegin().orElseThrow());
                return start != 0 ? start : right.getEnd().orElseThrow().compareTo(left.getEnd().orElseThrow());
            });
            int ordinal = 1;
            for (Node expression : expressions) {
                JsonObject call = expression instanceof MethodCallExpr method
                    ? methodCall(source, method, ordinal)
                    : constructorCall(source, (ObjectCreationExpr) expression, ordinal);
                calls.add(call);
                ordinal++;
            }
        }
        return calls;
    }

    private JsonObject methodCall(CallableFact source, MethodCallExpr expression, int ordinal) {
        String name = expression.getNameAsString();
        String rendered = expression.getScope().map(scope -> scope + "." + name).orElse(name);
        List<CallableFact> candidates;
        if (expression.getScope().isEmpty()) {
            candidates = callablesByName.getOrDefault(name, List.of());
        } else {
            String scope = expression.getScope().orElseThrow().toString();
            String qualifiedName = ("this".equals(scope) ? source.owner() : scope) + "." + name;
            candidates = callablesByQualifiedName.getOrDefault(qualifiedName, List.of());
        }
        return call(source, ordinal, expression, rendered, name, candidates);
    }

    private JsonObject constructorCall(CallableFact source, ObjectCreationExpr expression, int ordinal) {
        String target = expression.getType().toString();
        List<CallableFact> candidates = constructorsByOwner.getOrDefault(target, List.of());
        return call(source, ordinal, expression, target, lastPart(target), candidates);
    }

    private JsonObject call(
        CallableFact source,
        int ordinal,
        Node expression,
        String rendered,
        String targetName,
        List<CallableFact> candidates
    ) {
        JsonObject call = new JsonObject();
        call.add("source_callable_id", source.json().getAsJsonObject("declaration_id").deepCopy());
        call.addProperty("ordinal", ordinal);
        call.add(
            "target_callable_id",
            candidates.size() == 1
                ? candidates.get(0).json().getAsJsonObject("declaration_id").deepCopy()
                : JsonNull.INSTANCE
        );
        call.addProperty("source_id", sourceId);
        call.addProperty("line", beginLine(expression));
        call.addProperty("expression", rendered);
        call.addProperty("resolution", candidates.size() == 1 ? "resolved" : "unresolved");
        call.addProperty("target_name", targetName);
        return call;
    }

    private boolean belongsTo(Node expression, Node owner) {
        Optional<Node> current = expression.getParentNode();
        while (current.isPresent()) {
            Node candidate = current.get();
            if (candidate instanceof CallableDeclaration<?> || candidate instanceof CompactConstructorDeclaration) {
                return candidate == owner;
            }
            current = candidate.getParentNode();
        }
        return false;
    }

    private JsonObject declarationIdentity(String family, String qualifiedName, int ordinal) {
        JsonObject identity = new JsonObject();
        identity.addProperty("source_id", sourceId);
        identity.addProperty("family", family);
        identity.addProperty("qualified_name", qualifiedName);
        identity.addProperty("ordinal", ordinal);
        return identity;
    }

    private DeclarationKind declarationKind(TypeDeclaration<?> declaration) {
        if (declaration.isClassOrInterfaceDeclaration()) {
            ClassOrInterfaceDeclaration typed = declaration.asClassOrInterfaceDeclaration();
            if (typed.isInterface()) {
                return new DeclarationKind("interface", "interface");
            }
            return typed.isAbstract()
                ? new DeclarationKind("abstract_class", "abstract_class")
                : new DeclarationKind("class", "class");
        }
        if (declaration.isRecordDeclaration()) {
            return new DeclarationKind("record", "class");
        }
        if (declaration.isEnumDeclaration()) {
            return new DeclarationKind("enum", "class");
        }
        if (declaration.isAnnotationDeclaration()) {
            return new DeclarationKind("annotation", "interface");
        }
        throw new IllegalArgumentException("Unsupported Java declaration: " + declaration.getClass().getSimpleName());
    }

    private String implicitTypeVisibility(TypeDeclaration<?> declaration) {
        Optional<Node> parent = declaration.getParentNode();
        if (parent.isPresent() && parent.get() instanceof ClassOrInterfaceDeclaration owner && owner.isInterface()) {
            return "public";
        }
        if (parent.isPresent() && parent.get() instanceof AnnotationDeclaration) {
            return "public";
        }
        return "internal";
    }

    private String visibility(NodeWithModifiers<?> node, String fallback) {
        if (node.hasModifier(com.github.javaparser.ast.Modifier.Keyword.PUBLIC)) {
            return "public";
        }
        if (node.hasModifier(com.github.javaparser.ast.Modifier.Keyword.PROTECTED)) {
            return "protected";
        }
        if (node.hasModifier(com.github.javaparser.ast.Modifier.Keyword.PRIVATE)) {
            return "private";
        }
        return fallback;
    }

    private JsonArray annotationsForNode(Node node) {
        if (node instanceof BodyDeclaration<?> declaration) {
            return annotations(declaration.getAnnotations());
        }
        return new JsonArray();
    }

    private JsonArray annotations(Iterable<AnnotationExpr> annotations) {
        JsonArray result = new JsonArray();
        for (AnnotationExpr annotation : annotations) {
            result.add(annotation.toString());
        }
        return result;
    }

    private int publicSymbolCount(JsonArray declarations) {
        int count = 0;
        for (JsonElement declaration : declarations) {
            if ("public".equals(declaration.getAsJsonObject().get("visibility").getAsString())) {
                count += 1;
            }
        }
        return count;
    }

    private int codeLineCount(String content) {
        int count = 0;
        boolean inBlockComment = false;
        for (String line : content.split("\\R", -1)) {
            String remaining = line.strip();
            if (inBlockComment) {
                int end = remaining.indexOf("*/");
                if (end < 0) {
                    continue;
                }
                remaining = remaining.substring(end + 2).strip();
                inBlockComment = false;
            }
            while (remaining.startsWith("/*")) {
                int end = remaining.indexOf("*/", 2);
                if (end < 0) {
                    inBlockComment = true;
                    remaining = "";
                    break;
                }
                remaining = remaining.substring(end + 2).strip();
            }
            if (!remaining.isEmpty() && !remaining.startsWith("//")) {
                count += 1;
            }
        }
        return count;
    }

    private int ordinal(Node node) {
        return beginLine(node) * 10000 + beginColumn(node);
    }

    private int beginLine(Node node) {
        return node.getRange().map(range -> range.begin.line).orElse(1);
    }

    private int beginColumn(Node node) {
        return node.getRange().map(range -> range.begin.column).orElse(1);
    }

    private int endLine(Node node) {
        return node.getRange().map(range -> range.end.line).orElse(beginLine(node));
    }

    private int lineCount(Node node) {
        return endLine(node) - beginLine(node) + 1;
    }

    private String parentPath(String value) {
        int separator = value.lastIndexOf('/');
        return separator < 0 ? value : value.substring(0, separator);
    }

    private String lastPart(String value) {
        int slash = value.lastIndexOf('/');
        int dot = value.lastIndexOf('.');
        int separator = Math.max(slash, dot);
        return separator < 0 ? value : value.substring(separator + 1);
    }

    private record DeclarationKind(String kind, String family) {}

    private record CallableFact(
        Node node,
        JsonObject json,
        String name,
        String owner,
        String qualifiedName,
        boolean constructor
    ) {}
}

final class SourceParseFailure extends RuntimeException {
    private final String path;
    private final int line;
    private final int column;
    private final String diagnostic;

    SourceParseFailure(String path, int line, int column, String diagnostic, Throwable cause) {
        super(diagnostic, cause);
        this.path = path;
        this.line = line;
        this.column = column;
        this.diagnostic = diagnostic;
    }

    JsonObject document() {
        JsonObject document = new JsonObject();
        document.addProperty("code", "source_parse");
        document.addProperty("language", "java");
        document.addProperty("path", path);
        document.addProperty("line", line);
        document.addProperty("column", column);
        document.addProperty("diagnostic", diagnostic);
        return document;
    }
}

final class ExtractorInvariantFailure extends RuntimeException {
    ExtractorInvariantFailure(String message, Throwable cause) {
        super(message, cause);
    }
}
