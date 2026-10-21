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
        result.add("callables", callables);
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
        String visibility = visibility(declaration, implicitTypeVisibility(declaration));
        JsonArray methods = new JsonArray();
        JsonArray abstractMethods = new JsonArray();
        JsonArray properties = new JsonArray();

        collectProperties(declaration, properties);
        collectCallableDeclarations(declaration, qualifiedName, methods, abstractMethods, callables);

        JsonObject identity = declarationIdentity(kind.family(), qualifiedName, ordinal(declaration));
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

    private void collectProperties(TypeDeclaration<?> declaration, JsonArray properties) {
        boolean implicitStaticFields = (
            declaration.isClassOrInterfaceDeclaration()
                && declaration.asClassOrInterfaceDeclaration().isInterface()
        ) || declaration.isAnnotationDeclaration();
        for (FieldDeclaration field : declaration.getFields()) {
            String fallback = implicitStaticFields ? "public" : "internal";
            for (VariableDeclarator variable : field.getVariables()) {
                properties.add(property(
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
                    component.getNameAsString(),
                    component.getType().toString(),
                    "public",
                    "instance"
                ));
            }
        }
        if (declaration.isEnumDeclaration()) {
            for (EnumConstantDeclaration entry : declaration.asEnumDeclaration().getEntries()) {
                properties.add(property(entry.getNameAsString(), declaration.getNameAsString(), "public", "static"));
            }
        }
        if (declaration.isAnnotationDeclaration()) {
            for (BodyDeclaration<?> member : declaration.getMembers()) {
                if (member.isAnnotationMemberDeclaration()) {
                    AnnotationMemberDeclaration annotationMember = member.asAnnotationMemberDeclaration();
                    properties.add(property(
                        annotationMember.getNameAsString(),
                        annotationMember.getType().toString(),
                        "public",
                        "instance"
                    ));
                }
            }
        }
    }

    private JsonObject property(String name, String annotation, String visibility, String memberKind) {
        JsonObject value = new JsonObject();
        value.addProperty("kind", "unsupported");
        value.addProperty("expression", "");
        value.addProperty("reference", "");
        JsonArray assignedValues = new JsonArray();
        assignedValues.add(value);

        JsonObject property = new JsonObject();
        property.addProperty("name", name);
        property.addProperty("is_optional", false);
        property.addProperty("annotation", annotation);
        property.addProperty("visibility", visibility);
        property.addProperty("member_kind", memberKind);
        property.add("assigned_values", assignedValues);
        return property;
    }

    private void collectCallableDeclarations(
        TypeDeclaration<?> declaration,
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
            JsonObject summary = methodSummary(
                constructor,
                "constructor",
                visibility(constructor, constructorFallback)
            );
            methods.add(summary);
            addCallable(
                constructor,
                "constructor",
                owner,
                "constructor",
                "",
                visibility(constructor, constructorFallback),
                callables
            );
        }
        if (declaration.isRecordDeclaration()) {
            RecordDeclaration record = declaration.asRecordDeclaration();
            for (CompactConstructorDeclaration constructor : record.getCompactConstructors()) {
                String constructorVisibility = visibility(
                    constructor,
                    visibility(record, implicitTypeVisibility(record))
                );
                methods.add(compactConstructorSummary(constructor, record.getParameters(), constructorVisibility));
                addCompactConstructor(constructor, record.getParameters(), owner, constructorVisibility, callables);
            }
        }
        for (MethodDeclaration method : declaration.getMethods()) {
            String methodVisibility = visibility(method, methodFallback);
            JsonObject summary = methodSummary(method, method.getNameAsString(), methodVisibility);
            if (!interfaceDeclaration && (method.isAbstract() || method.getBody().isEmpty())) {
                abstractMethods.add(summary);
            } else {
                methods.add(summary);
            }
            addCallable(
                method,
                method.getNameAsString(),
                owner,
                method.isStatic() ? "static_method" : "instance_method",
                method.getType().toString(),
                methodVisibility,
                callables
            );
        }
        if (declaration.isAnnotationDeclaration()) {
            for (BodyDeclaration<?> member : declaration.getMembers()) {
                if (member.isAnnotationMemberDeclaration()) {
                    AnnotationMemberDeclaration annotationMember = member.asAnnotationMemberDeclaration();
                    JsonObject summary = annotationMemberSummary(annotationMember);
                    abstractMethods.add(summary);
                    addAnnotationCallable(annotationMember, owner, callables);
                }
            }
        }
    }

    private JsonObject methodSummary(
        CallableDeclaration<?> declaration,
        String name,
        String visibility
    ) {
        JsonObject summary = new JsonObject();
        summary.addProperty("name", name);
        summary.addProperty("visibility", visibility);
        summary.addProperty("visibility_intent", visibility);
        summary.add("declaration_annotations", annotations(declaration.getAnnotations()));
        summary.addProperty("line_count", lineCount(declaration));
        summary.addProperty("declared_args", declaration.getParameters().size());
        summary.addProperty("optional_args", 0);
        return summary;
    }

    private JsonObject annotationMemberSummary(AnnotationMemberDeclaration declaration) {
        JsonObject summary = new JsonObject();
        summary.addProperty("name", declaration.getNameAsString());
        summary.addProperty("visibility", "public");
        summary.addProperty("visibility_intent", "public");
        summary.add("declaration_annotations", annotations(declaration.getAnnotations()));
        summary.addProperty("line_count", lineCount(declaration));
        summary.addProperty("declared_args", 0);
        summary.addProperty("optional_args", 0);
        return summary;
    }

    private JsonObject compactConstructorSummary(
        CompactConstructorDeclaration declaration,
        List<Parameter> parameters,
        String visibility
    ) {
        JsonObject summary = new JsonObject();
        summary.addProperty("name", "constructor");
        summary.addProperty("visibility", visibility);
        summary.addProperty("visibility_intent", visibility);
        summary.add("declaration_annotations", annotations(declaration.getAnnotations()));
        summary.addProperty("line_count", lineCount(declaration));
        summary.addProperty("declared_args", parameters.size());
        summary.addProperty("optional_args", 0);
        return summary;
    }

    private void addCallable(
        CallableDeclaration<?> declaration,
        String name,
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
            owner,
            qualifiedName,
            kind,
            returnAnnotation,
            visibility,
            ordinal
        );
        callables.add(callable);
        callableFacts.add(new CallableFact(declaration, callable, name, owner, qualifiedName, "constructor".equals(kind)));
    }

    private void addAnnotationCallable(
        AnnotationMemberDeclaration declaration,
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
            owner,
            qualifiedName,
            "instance_method",
            declaration.getType().toString(),
            "public",
            ordinal
        );
        callables.add(callable);
        callableFacts.add(new CallableFact(declaration, callable, name, owner, qualifiedName, false));
    }

    private void addCompactConstructor(
        CompactConstructorDeclaration declaration,
        List<Parameter> parameters,
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
            owner,
            qualifiedName,
            "constructor",
            "",
            visibility,
            ordinal
        );
        callables.add(callable);
        callableFacts.add(new CallableFact(declaration, callable, "constructor", owner, qualifiedName, true));
    }

    private JsonObject callable(
        Node declaration,
        List<Parameter> parameters,
        String name,
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
        callable.addProperty("owner_name", owner);
        callable.addProperty("kind", kind);
        callable.addProperty("visibility", visibility);
        callable.addProperty("visibility_intent", visibility);
        callable.add("declaration_annotations", annotationsForNode(declaration));
        callable.addProperty("line_start", beginLine(declaration));
        callable.addProperty("line_end", endLine(declaration));
        callable.addProperty("line_count", lineCount(declaration));
        callable.add("parameters", parameters(parameters));
        callable.addProperty("declared_args", parameters.size());
        callable.addProperty("optional_args", 0);
        callable.addProperty("return_annotation", returnAnnotation);
        callable.add("decorators", annotationsForNode(declaration));
        callable.addProperty("docstring", "");
        return callable;
    }

    private JsonArray parameters(List<Parameter> parameters) {
        JsonArray result = new JsonArray();
        for (Parameter parameter : parameters) {
            JsonObject fact = new JsonObject();
            fact.addProperty("name", parameter.getNameAsString());
            fact.addProperty("annotation", parameter.getType().toString());
            fact.addProperty("kind", parameter.isVarArgs() ? "variadic_positional" : "positional");
            fact.addProperty("has_default", false);
            result.add(fact);
        }
        return result;
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
            for (MethodCallExpr expression : source.node().findAll(MethodCallExpr.class)) {
                if (belongsTo(expression, source.node())) {
                    calls.add(methodCall(source, expression));
                }
            }
            for (ObjectCreationExpr expression : source.node().findAll(ObjectCreationExpr.class)) {
                if (belongsTo(expression, source.node())) {
                    calls.add(constructorCall(source, expression));
                }
            }
        }
        return calls;
    }

    private JsonObject methodCall(CallableFact source, MethodCallExpr expression) {
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
        return call(source, expression, rendered, name, candidates);
    }

    private JsonObject constructorCall(CallableFact source, ObjectCreationExpr expression) {
        String target = expression.getType().toString();
        List<CallableFact> candidates = constructorsByOwner.getOrDefault(target, List.of());
        return call(source, expression, target, lastPart(target), candidates);
    }

    private JsonObject call(
        CallableFact source,
        Node expression,
        String rendered,
        String targetName,
        List<CallableFact> candidates
    ) {
        JsonObject call = new JsonObject();
        call.add("source_callable_id", source.json().getAsJsonObject("declaration_id").deepCopy());
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
