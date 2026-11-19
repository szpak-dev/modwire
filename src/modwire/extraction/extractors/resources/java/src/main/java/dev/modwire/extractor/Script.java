package dev.modwire.extractor;

import com.github.javaparser.ParserConfiguration;
import com.github.javaparser.ParseProblemException;
import com.github.javaparser.Problem;
import com.github.javaparser.Range;
import com.github.javaparser.JavaParser;
import com.github.javaparser.JavaParserAdapter;
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
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonPrimitive;
import com.google.gson.stream.JsonWriter;
import java.io.BufferedWriter;
import java.io.OutputStreamWriter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.IdentityHashMap;
import java.util.HexFormat;
import java.util.Iterator;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import com.github.javaparser.ast.stmt.BlockStmt;
import com.github.javaparser.ast.stmt.CatchClause;
import com.github.javaparser.ast.stmt.ForStmt;
import com.github.javaparser.ast.stmt.ForEachStmt;
import com.github.javaparser.ast.stmt.TryStmt;
import com.github.javaparser.ast.expr.LambdaExpr;
import com.github.javaparser.ast.expr.MethodReferenceExpr;

public final class Script {

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
        JsonElement input = JsonParser.parseReader(
            new java.io.InputStreamReader(System.in, StandardCharsets.UTF_8)
        );
        if (!input.isJsonObject()) {
            throw new IllegalArgumentException("Expected a JSON object mapping source ids to Java file paths.");
        }
        BufferedWriter output = new BufferedWriter(new OutputStreamWriter(System.out, StandardCharsets.UTF_8), 65536);
        int workers = 2;
        ExecutorService executor = Executors.newFixedThreadPool(workers);
        ArrayDeque<Future<NativeFileResult>> pending = new ArrayDeque<>();
        Iterator<Map.Entry<String, JsonElement>> sources = input.getAsJsonObject().entrySet().iterator();
        try {
            for (int worker = 0; worker < workers && sources.hasNext(); worker++) {
                pending.addLast(submit(executor, new JavaSourceExtractor(), sources.next()));
            }
            while (!pending.isEmpty()) {
                NativeFileResult result = complete(pending.removeFirst());
                result.extractor().writeRecord(new JsonWriter(output), result.facts());
                output.write('\n');
                output.flush();
                if (sources.hasNext()) {
                    pending.addLast(submit(executor, result.extractor(), sources.next()));
                }
            }
        } finally {
            for (Future<NativeFileResult> result : pending) result.cancel(true);
            executor.shutdownNow();
        }
    }

    private Future<NativeFileResult> submit(
        ExecutorService executor, JavaSourceExtractor extractor, Map.Entry<String, JsonElement> entry
    ) {
        if (!entry.getValue().isJsonPrimitive() || !entry.getValue().getAsJsonPrimitive().isString()) {
            throw new IllegalArgumentException("Expected source ids and paths to be strings.");
        }
        return executor.submit(() -> new NativeFileResult(
            extractor, extractor.extract(Path.of(entry.getValue().getAsString()), entry.getKey())
        ));
    }

    private NativeFileResult complete(Future<NativeFileResult> pending) throws IOException {
        try {
            return pending.get();
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new ExtractorInvariantFailure("Java extraction worker was interrupted.", error);
        } catch (ExecutionException error) {
            Throwable cause = error.getCause();
            if (cause instanceof IOException failure) throw failure;
            if (cause instanceof RuntimeException failure) throw failure;
            if (cause instanceof Error failure) throw failure;
            throw new ExtractorInvariantFailure("Java extraction worker raised an unexpected checked failure.", cause);
        }
    }
}

record NativeFileResult(JavaSourceExtractor extractor, JsonObject facts) {}

final class NativeValueTable {
    final String name;
    final List<JsonElement> values = new ArrayList<>();

    NativeValueTable(String name) {
        this.name = name;
    }

    <T extends JsonElement> T add(T value) {
        values.add(value);
        return value;
    }
}

final class NativeSourceRecord {
    final NativeValueTable texts = new NativeValueTable("texts");
    final NativeValueTable identities = new NativeValueTable("identities");
    final NativeValueTable targets = new NativeValueTable("targets");
    final NativeValueTable types = new NativeValueTable("types");
    final NativeValueTable coverages = new NativeValueTable("coverages");
    final NativeValueTable memberInventories = new NativeValueTable("member_inventories");
    final NativeValueTable namespaces = new NativeValueTable("namespaces");
    final NativeValueTable placements = new NativeValueTable("placements");
    final NativeValueTable assignments = new NativeValueTable("assignments");
    final NativeValueTable parameters = new NativeValueTable("parameters");
    private final Map<JsonElement, Integer> references = new IdentityHashMap<>();

    void write(JsonWriter output, String sourceId, JsonObject facts) throws IOException {
        output.setSerializeNulls(true);
        output.beginObject().name("source_id").value(sourceId);
        int offset = 0;
        for (NativeValueTable table : List.of(texts, identities, targets, types, coverages,
                memberInventories, namespaces, placements, assignments, parameters)) {
            Map<JsonElement, Integer> unique = new LinkedHashMap<>();
            int tableOffset = offset;
            for (JsonElement value : table.values) {
                int index = unique.computeIfAbsent(value, key -> tableOffset + unique.size());
                references.put(value, index);
            }
            output.name(table.name).beginArray();
            for (JsonElement value : unique.keySet()) writeValue(output, value, offset);
            output.endArray();
            offset += unique.size();
        }
        output.name("facts");
        writeValue(output, facts, offset);
        output.endObject();
    }

    private void writeValue(JsonWriter output, JsonElement value, int referenceLimit) throws IOException {
        Integer reference = references.get(value);
        if (reference != null && reference < referenceLimit) {
            output.value(reference);
        } else if (value.isJsonObject()) {
            output.beginObject();
            for (Map.Entry<String, JsonElement> entry : value.getAsJsonObject().entrySet()) {
                output.name(entry.getKey());
                writeValue(output, entry.getValue(), referenceLimit);
            }
            output.endObject();
        } else if (value.isJsonArray()) {
            output.beginArray();
            for (JsonElement child : value.getAsJsonArray()) writeValue(output, child, referenceLimit);
            output.endArray();
        } else if (value.isJsonNull()) {
            output.nullValue();
        } else {
            JsonPrimitive primitive = value.getAsJsonPrimitive();
            if (primitive.isString()) output.value(primitive.getAsString());
            else if (primitive.isBoolean()) output.value(primitive.getAsBoolean());
            else output.value(primitive.getAsNumber());
        }
    }
}

final class JavaSourceExtractor {
    private final JavaParserAdapter parser = JavaParserAdapter.of(new JavaParser(
        new ParserConfiguration().setLanguageLevel(ParserConfiguration.LanguageLevel.JAVA_25)
    ));
    private final List<CallableFact> callableFacts = new ArrayList<>();
    private NativeSourceRecord record = new NativeSourceRecord();
    private JsonElement sourceIdValue = JsonNull.INSTANCE;
    private JsonElement contentDigestValue = JsonNull.INSTANCE;
    private String sourceId = "";
    private String contentDigest = "";
    private String sourceContent = "";
    private int[] lineOffsets = new int[0];
    private int[] utf8Offsets = new int[0];
    private final Map<Node, JsonObject> identities = new IdentityHashMap<>();
    private final Map<Node, Map<String, List<Node>>> declarationBindings = new IdentityHashMap<>();
    private final Map<Node, Map<String, List<Node>>> valueBindings = new IdentityHashMap<>();
    private final Map<BlockStmt, BlockSpan> blockSpans = new IdentityHashMap<>();
    private JsonObject namespaceMembership = new JsonObject();
    private JsonObject inventory = new JsonObject();

    JsonObject extract(Path path, String sourceIdentity) throws IOException {
        sourceId = sourceIdentity;
        record = new NativeSourceRecord();
        sourceIdValue = record.texts.add(new JsonPrimitive(sourceId));
        identities.clear();
        declarationBindings.clear();
        valueBindings.clear();
        blockSpans.clear();
        inventory = fileInventory();
        namespaceMembership = new JsonObject();
        namespaceMembership.addProperty("kind", "none");
        record.namespaces.add(namespaceMembership);
        callableFacts.clear();

        String content = Files.readString(path, StandardCharsets.UTF_8);
        sourceContent = content;
        indexSourcePositions();
        try {
            contentDigest = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(content.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException error) {
            throw new ExtractorInvariantFailure("SHA-256 is unavailable.", error);
        }
        contentDigestValue = record.texts.add(new JsonPrimitive(contentDigest));
        CompilationUnit unit;
        try {
            unit = parser.parse(content);
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

        JsonArray values = new JsonArray();
        JsonArray callableValues = new JsonArray();
        JsonArray anonymousCallables = new JsonArray();
        unit.walk(node -> {
            if (node instanceof Parameter parameter) indexValueBinding(parameter.getNameAsString(), parameter);
            else if (node instanceof VariableDeclarator variable) indexValueBinding(variable.getNameAsString(), variable);
            if (node instanceof TypeDeclaration<?> declaration) {
                collectType(declaration, ownerName(node, unit), declarations, callables, relations);
            } else if (node instanceof ObjectCreationExpr creation && creation.getAnonymousClassBody().isPresent()) {
                collectAnonymousType(creation, creation.getAnonymousClassBody().get(), ownerName(node, unit), declarations, callables);
                relations.add(relation(identities.get(node), "extends", creation.getType().toString()));
            } else if (node instanceof EnumConstantDeclaration constant && !constant.getClassBody().isEmpty()) {
                collectAnonymousType(constant, constant.getClassBody(), ownerName(node, unit), declarations, callables);
            } else if (node instanceof LambdaExpr lambda) {
                String owner = ownerName(node, unit);
                Node parent = lambda.getParentNode().orElseThrow(() -> new ExtractorInvariantFailure("Lambda has no native parent.", null));
                boolean bound = parent instanceof VariableDeclarator;
                String name = bound ? ((VariableDeclarator) parent).getNameAsString() : "<anonymous>@" + ordinal(lambda);
                String qualified = owner.isEmpty() ? name : owner + "." + name;
                JsonObject fact = callable(lambda, lambda.getParameters(), name, new JsonObject(), owner, qualified,
                    bound ? "callable_value" : "anonymous", "", "private", ordinal(lambda));
                if (bound) {
                    fact.addProperty("declaration_kind", "assignment"); fact.addProperty("value_kind", "value_callable");
                    fact.addProperty("scope", parent.getParentNode().filter(FieldDeclaration.class::isInstance).isPresent() ? "member" : "local");
                    callableValues.add(fact);
                } else anonymousCallables.add(fact);
                callableFacts.add(new CallableFact(lambda, fact, name, owner, qualified, false));
            } else if (node instanceof VariableDeclarator variable && variable.getParentNode().filter(FieldDeclaration.class::isInstance).isEmpty()
                && variable.getInitializer().filter(LambdaExpr.class::isInstance).isEmpty()) {
                values.add(value(variable, ownerName(node, unit)));
            } else if (node instanceof MethodReferenceExpr) {
                limitInventory("callable_values", node, "Method references require a resolved external binding and do not declare a callable body.");
            }
        });
        for (Map.Entry<Node, JsonObject> entry : identities.entrySet()) {
            declarationBindings.computeIfAbsent(bindingScope(entry.getKey()), scope -> new HashMap<>())
                .computeIfAbsent(lastPart(entry.getValue().get("qualified_name").getAsString()), name -> new ArrayList<>())
                .add(entry.getKey());
        }
        for (JsonElement value : relations) {
            JsonObject relation = value.getAsJsonObject();
            Node source = identities.entrySet().stream()
                .filter(entry -> entry.getValue() == relation.getAsJsonObject("source_declaration_id"))
                .map(Map.Entry::getKey).findFirst()
                .orElseThrow(() -> new ExtractorInvariantFailure("Relation source has no indexed native declaration.", null));
            relation.add("target", resolveTarget(relation.get("target_reference").getAsString(), source, false));
        }

        JsonObject result = new JsonObject();
        result.add("inventory", inventory);
        result.add("unresolved_methods", new JsonArray());
        result.add("imports", imports(unit));
        result.add("exports", new JsonArray());
        result.add("namespaces", namespaces);
        result.add("declarations", declarations);
        result.add("functions", new JsonArray());
        result.add("values", values);
        result.add("callable_values", callableValues);
        result.add("anonymous_callables", anonymousCallables);
        result.add("calls", calls());
        result.add("declaration_relations", relations);
        String[] lines = content.split("\\R", -1);
        result.addProperty("line_count", lines.length);
        result.addProperty("code_line_count", codeLineCount(lines));
        result.addProperty("public_symbol_count", publicSymbolCount(declarations));
        return result;
    }

    void writeRecord(JsonWriter output, JsonObject facts) throws IOException {
        record.write(output, sourceId, facts);
    }

    private JsonArray namespaces(CompilationUnit unit) {
        JsonArray namespaces = new JsonArray();
        unit.getPackageDeclaration().ifPresent(declaration -> {
            JsonObject namespace = new JsonObject();
            namespace.addProperty("kind", "package");
            JsonObject identity = declarationIdentity("namespace", declaration.getNameAsString(), ordinal(declaration));
            namespace.add("declaration_id", identity);
            namespace.add("placement", placement(declaration));
            namespaceMembership = new JsonObject();
            record.namespaces.add(namespaceMembership);
            namespaceMembership.addProperty("kind", "member");
            namespaceMembership.addProperty("namespace_reference", declaration.getNameAsString());
            JsonObject target = new JsonObject();
            target.addProperty("kind", "resolved");
            target.add("declaration_id", identity);
            namespaceMembership.add("target", record.targets.add(target));
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
        identities.put(declaration, identity);
        String visibility = visibility(declaration, implicitTypeVisibility(declaration));
        JsonArray methods = new JsonArray();
        JsonArray abstractMethods = new JsonArray();
        JsonArray properties = new JsonArray();

        collectProperties(declaration, identity, properties);
        collectCallableDeclarations(declaration, declaration.getMembers(), identity, qualifiedName, methods, abstractMethods, callables);

        JsonObject fact = new JsonObject();
        fact.add("declaration_id", identity);
        fact.add("placement", placement(declaration));
        fact.add("inventory", memberInventory());
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
        assignedValues.add(record.assignments.add(value));

        JsonObject property = new JsonObject();
        property.add(
            "declaration_id",
            declarationIdentity(
                "property",
                ownerIdentity.get("qualified_name").getAsString() + "." + name,
                ordinal(declaration)
            )
        );
        property.add("owner_declaration_id", ownerIdentity);
        property.add("placement", placement(declaration));
        property.addProperty("name", name);
        property.addProperty("is_optional", false);
        property.add("type", sourceType(annotation));
        property.addProperty("visibility", visibility);
        property.addProperty("member_kind", memberKind);
        property.add("assigned_values", assignedValues);
        return property;
    }

    private void collectCallableDeclarations(
        Node declaration,
        List<BodyDeclaration<?>> members,
        JsonObject ownerIdentity,
        String owner,
        JsonArray methods,
        JsonArray abstractMethods,
        JsonArray callables
    ) {
        boolean interfaceDeclaration = declaration instanceof ClassOrInterfaceDeclaration typed && typed.isInterface();
        String methodFallback = interfaceDeclaration ? "public" : "internal";
        String constructorFallback = declaration instanceof EnumDeclaration ? "private" : methodFallback;
        for (BodyDeclaration<?> member : members) {
            if (member instanceof ConstructorDeclaration constructor) {
                methods.add(addCallable(constructor, "constructor", ownerIdentity, owner, "constructor", "",
                    visibility(constructor, constructorFallback), callables));
            } else if (member instanceof CompactConstructorDeclaration constructor && declaration instanceof RecordDeclaration record) {
                methods.add(addCompactConstructor(constructor, record.getParameters(), ownerIdentity, owner,
                    visibility(constructor, visibility(record, implicitTypeVisibility(record))), callables));
            } else if (member instanceof MethodDeclaration method) {
                JsonObject callable = addCallable(method, method.getNameAsString(), ownerIdentity, owner,
                    method.isStatic() ? "static_method" : "instance_method", method.getType().toString(), visibility(method, methodFallback), callables);
                if (method.isAbstract() || method.getBody().isEmpty()) abstractMethods.add(callable);
                else methods.add(callable);
            } else if (member instanceof AnnotationMemberDeclaration annotation) {
                abstractMethods.add(addAnnotationCallable(annotation, ownerIdentity, owner, callables));
            }
        }
    }

    private void collectAnonymousType(Node node, List<BodyDeclaration<?>> members, String owner, JsonArray declarations, JsonArray callables) {
        String name = "<anonymous>@" + ordinal(node);
        String qualified = owner.isEmpty() ? name : owner + "." + name;
        JsonObject identity = declarationIdentity("class", qualified, ordinal(node));
        identities.put(node, identity);
        JsonArray methods = new JsonArray(); JsonArray abstractMethods = new JsonArray(); JsonArray properties = new JsonArray();
        collectCallableDeclarations(node, members, identity, qualified, methods, abstractMethods, callables);
        for (BodyDeclaration<?> member : members) if (member instanceof FieldDeclaration field) {
            for (VariableDeclarator variable : field.getVariables()) properties.add(property(variable, identity, variable.getNameAsString(),
                variable.getType().toString(), visibility(field, "internal"), field.isStatic() ? "static" : "instance"));
        }
        JsonObject fact = new JsonObject();
        fact.add("declaration_id", identity); fact.add("placement", placement(node)); fact.add("inventory", memberInventory());
        fact.addProperty("kind", "class"); fact.addProperty("name", name); fact.addProperty("visibility", "private"); fact.addProperty("visibility_intent", "private");
        fact.add("declaration_annotations", new JsonArray()); fact.addProperty("line_count", lineCount(node));
        fact.add("methods", methods); fact.add("abstract_methods", abstractMethods); fact.add("properties", properties); fact.add("signatures", new JsonArray());
        declarations.add(fact);
    }

    private JsonObject value(VariableDeclarator variable, String owner) {
        String name = variable.getNameAsString(); String qualified = owner.isEmpty() ? name : owner + "." + name;
        JsonObject fact = new JsonObject();
        fact.add("declaration_id", declarationIdentity("value", qualified, ordinal(variable))); fact.add("placement", placement(variable));
        fact.addProperty("name", name); fact.addProperty("visibility", "private"); fact.addProperty("visibility_intent", "private");
        fact.addProperty("line_count", lineCount(variable)); fact.addProperty("declaration_kind", "assignment");
        fact.addProperty("value_kind", "value_unknown"); fact.addProperty("scope", "local");
        return fact;
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
        long ordinal = ordinal(declaration);
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
        long ordinal = ordinal(declaration);
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
        long ordinal = ordinal(declaration);
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
        long ordinal
    ) {
        JsonObject callable = new JsonObject();
        String family = "callable_value".equals(kind) ? "value" : "anonymous".equals(kind) ? "callable" : "method";
        JsonObject identity = declarationIdentity(family, qualifiedName, ordinal);
        identities.put(declaration, identity);
        callable.add("declaration_id", identity);
        callable.add("placement", placement(declaration));
        callable.add("source_id", sourceIdValue);
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
        if ("method".equals(family)) callable.add("owner_declaration_id", ownerIdentity);
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
            result.add(record.parameters.add(fact));
        }
        return result;
    }

    private JsonObject sourceType(String authoredType) {
        String value = authoredType.strip();
        JsonObject type = new JsonObject();
        if (value.isEmpty()) {
            type.addProperty("kind", "absent");
            return record.types.add(type);
        }
        if (value.contains("?") || value.contains("[") || value.contains("&") || value.contains("|")) {
            type.addProperty("kind", "unsupported");
            return record.types.add(type);
        }
        int genericStart = value.indexOf('<');
        if (genericStart < 0) {
            type.addProperty("kind", "reference");
            type.addProperty("name", value);
            type.add("arguments", new JsonArray());
            return record.types.add(type);
        }
        if (!value.endsWith(">")) {
            type.addProperty("kind", "unsupported");
            return record.types.add(type);
        }
        String name = value.substring(0, genericStart).strip();
        List<String> arguments = genericArguments(value.substring(genericStart + 1, value.length() - 1));
        if (name.isEmpty() || arguments.isEmpty()) {
            type.addProperty("kind", "unsupported");
            return record.types.add(type);
        }
        JsonArray typeArguments = new JsonArray();
        for (String argument : arguments) {
            typeArguments.add(sourceType(argument));
        }
        type.addProperty("kind", "reference");
        type.addProperty("name", name);
        type.add("arguments", typeArguments);
        return record.types.add(type);
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
        relation.add("source_declaration_id", identity);
        relation.addProperty("kind", kind);
        relation.addProperty("target_reference", target);
        return relation;
    }

    private JsonArray calls() {
        JsonArray calls = new JsonArray();
        for (CallableFact source : callableFacts) {
            List<Node> expressions = new ArrayList<>();
            source.node().walk(expression -> {
                if ((expression instanceof MethodCallExpr || expression instanceof ObjectCreationExpr)
                    && belongsTo(expression, source.node())) {
                    expressions.add(expression);
                }
            });
            expressions.sort((left, right) -> {
                int start = sourceRange(left).begin.compareTo(sourceRange(right).begin);
                return start != 0 ? start : sourceRange(right).end.compareTo(sourceRange(left).end);
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
        JsonObject target = resolveTarget(rendered, expression, true);
        return call(source, ordinal, expression, rendered, name, targetCallables(target, false));
    }

    private JsonObject constructorCall(CallableFact source, ObjectCreationExpr expression, int ordinal) {
        String target = expression.getType().getNameWithScope();
        JsonObject binding = resolveTarget(target, expression, false);
        return call(source, ordinal, expression, target, lastPart(target), targetCallables(binding, true));
    }

    private List<CallableFact> targetCallables(JsonObject target, boolean constructor) {
        if (!target.get("kind").getAsString().equals("resolved")) return List.of();
        JsonObject identity = target.getAsJsonObject("declaration_id");
        return callableFacts.stream().filter(fact -> constructor
            ? fact.constructor() && fact.json().getAsJsonObject("owner_declaration_id") == identity
            : fact.json().getAsJsonObject("declaration_id") == identity).toList();
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
        call.add("source_callable_id", source.json().getAsJsonObject("declaration_id"));
        call.addProperty("ordinal", ordinal);
        call.add(
            "target_callable_id",
            candidates.size() == 1
                ? candidates.get(0).json().getAsJsonObject("declaration_id")
                : JsonNull.INSTANCE
        );
        call.add("source_id", sourceIdValue);
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
            if (candidate instanceof CallableDeclaration<?> || candidate instanceof CompactConstructorDeclaration || candidate instanceof LambdaExpr) {
                return candidate == owner;
            }
            current = candidate.getParentNode();
        }
        return false;
    }

    private JsonObject declarationIdentity(String family, String qualifiedName, long ordinal) {
        JsonObject identity = new JsonObject();
        identity.add("source_id", sourceIdValue);
        identity.add("content_digest", contentDigestValue);
        identity.addProperty("family", family);
        identity.addProperty("qualified_name", qualifiedName);
        identity.addProperty("ordinal", ordinal);
        return record.identities.add(identity);
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

    private int codeLineCount(String[] lines) {
        int count = 0;
        boolean inBlockComment = false;
        for (String line : lines) {
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

    private long ordinal(Node node) {
        return ((long) beginLine(node) << 32) + beginColumn(node);
    }

    private Range sourceRange(Node node) {
        return node.getRange().orElseThrow(() -> new ExtractorInvariantFailure(
            "Java parser omitted the source range for " + node.getClass().getSimpleName() + " in " + sourceId, null));
    }

    private String ownerName(Node node, CompilationUnit unit) {
        return nearestIdentity(node).map(value -> value.get("qualified_name").getAsString())
            .orElseGet(() -> unit.getPackageDeclaration().map(declaration -> declaration.getNameAsString()).orElse(""));
    }

    private Optional<JsonObject> nearestIdentity(Node node) {
        Optional<Node> parent = node.getParentNode();
        while (parent.isPresent()) {
            JsonObject identity = identities.get(parent.get());
            if (identity != null) return Optional.of(identity);
            parent = parent.get().getParentNode();
        }
        return Optional.empty();
    }

    private void indexSourcePositions() {
        int lines = 1;
        for (int index = 0; index < sourceContent.length(); index++) {
            if (endsLine(index)) lines++;
        }
        lineOffsets = new int[lines];
        utf8Offsets = new int[sourceContent.length() + 1];
        int line = 1;
        for (int index = 0; index < sourceContent.length(); index++) {
            char character = sourceContent.charAt(index);
            if (endsLine(index)) lineOffsets[line++] = index + 1;
            int width = character < 0x80 ? 1 : character < 0x800 ? 2 : 3;
            if (Character.isSurrogate(character)) {
                width = Character.isLowSurrogate(character) && index > 0
                    && Character.isHighSurrogate(sourceContent.charAt(index - 1)) ? 3 : 1;
            }
            utf8Offsets[index + 1] = utf8Offsets[index] + width;
        }
    }

    private boolean endsLine(int index) {
        char character = sourceContent.charAt(index);
        return character == '\n' || character == '\r'
            && (index + 1 == sourceContent.length() || sourceContent.charAt(index + 1) != '\n');
    }

    private int byteOffset(com.github.javaparser.Position position, boolean inclusiveEnd) {
        if (position.line < 1 || position.line > lineOffsets.length) {
            throw new ExtractorInvariantFailure("Java source range lies outside " + sourceId, null);
        }
        int offset = lineOffsets[position.line - 1] + position.column - 1 + (inclusiveEnd ? 1 : 0);
        if (offset > sourceContent.length()) throw new ExtractorInvariantFailure("Java source column lies outside " + sourceId, null);
        return utf8Offsets[offset];
    }

    private JsonObject placement(Node node) {
        JsonObject container = new JsonObject();
        Optional<JsonObject> parentIdentity = nearestIdentity(node);
        if (parentIdentity.isPresent()) {
            container.addProperty("kind", "declaration");
            container.add("declaration_id", parentIdentity.get());
        } else {
            container.addProperty("kind", "file");
        }
        JsonObject lexical = container;
        Optional<Node> parent = node.getParentNode();
        while (parent.isPresent() && !identities.containsKey(parent.get())) {
            if (parent.get() instanceof BlockStmt block) {
                lexical = new JsonObject();
                lexical.addProperty("kind", "block");
                lexical.add("container", container);
                BlockSpan span = blockSpan(block);
                lexical.addProperty("start_utf8_offset", span.startUtf8Offset());
                lexical.addProperty("end_utf8_offset", span.endUtf8Offset());
                break;
            }
            parent = parent.get().getParentNode();
        }
        JsonObject result = new JsonObject();
        result.add("lexical_scope", lexical);
        result.add("namespace", namespaceMembership);
        return record.placements.add(result);
    }

    private BlockSpan blockSpan(BlockStmt block) {
        return blockSpans.computeIfAbsent(block, node -> {
            Range range = sourceRange(node);
            return new BlockSpan(byteOffset(range.begin, false), byteOffset(range.end, true));
        });
    }

    private JsonObject coverage(String status) {
        JsonObject result = new JsonObject();
        result.addProperty("status", status);
        result.add("limitations", new JsonArray());
        return record.coverages.add(result);
    }

    private JsonObject fileInventory() {
        JsonObject result = new JsonObject();
        for (String name : List.of("declarations", "values", "callable_values", "anonymous_callables", "namespaces")) result.add(name, coverage("complete"));
        for (String name : List.of("functions", "exports", "unresolved_methods")) result.add(name, coverage("not_applicable"));
        return result;
    }

    private JsonObject memberInventory() {
        JsonObject result = new JsonObject();
        for (String name : List.of("methods", "abstract_methods", "properties")) result.add(name, coverage("complete"));
        result.add("signatures", coverage("not_applicable"));
        return record.memberInventories.add(result);
    }

    private void limitInventory(String family, Node node, String description) {
        JsonObject coverage = inventory.getAsJsonObject(family);
        coverage.addProperty("status", "incomplete");
        JsonObject limitation = new JsonObject();
        limitation.addProperty("kind", "unsupported_syntax");
        limitation.addProperty("description", description);
        JsonObject location = new JsonObject();
        location.addProperty("kind", "source");
        location.addProperty("start_line", beginLine(node));
        location.addProperty("end_line", endLine(node));
        limitation.add("location", location);
        coverage.getAsJsonArray("limitations").add(limitation);
    }

    private Node bindingScope(Node node) {
        Node current = node.getParentNode().orElseThrow(() -> new ExtractorInvariantFailure("Native binding has no parent.", null));
        while (!(current instanceof CompilationUnit) && !(current instanceof BlockStmt)
            && !(current instanceof ForStmt) && !(current instanceof ForEachStmt)
            && !(current instanceof CatchClause) && !(current instanceof TryStmt)
            && !(current instanceof TypeDeclaration<?>) && !(current instanceof CallableDeclaration<?>)
            && !(current instanceof LambdaExpr) && !(current instanceof CompactConstructorDeclaration)
            && !(current instanceof ObjectCreationExpr creation && creation.getAnonymousClassBody().isPresent())
            && !(current instanceof EnumConstantDeclaration constant && !constant.getClassBody().isEmpty())) {
            current = current.getParentNode().orElseThrow(() -> new ExtractorInvariantFailure("Native scope has no root.", null));
        }
        return current;
    }

    private void indexValueBinding(String name, Node node) {
        valueBindings.computeIfAbsent(bindingScope(node), scope -> new HashMap<>())
            .computeIfAbsent(name, key -> new ArrayList<>()).add(node);
    }

    private boolean visibleBinding(Node binding, Node scope, Node source) {
        return !(scope instanceof BlockStmt || scope instanceof ForStmt || scope instanceof ForEachStmt || scope instanceof TryStmt)
            || sourceRange(binding).begin.compareTo(sourceRange(source).begin) <= 0;
    }

    private boolean shadowsReceiver(String name, Node scope, Node source) {
        Map<String, List<Node>> names = valueBindings.get(scope);
        return names != null && names.containsKey(name)
            && names.get(name).stream().anyMatch(node -> visibleBinding(node, scope, source));
    }

    private List<Node> bindings(String name, Node scope, Node source, boolean valueReference) {
        Map<String, List<Node>> names = declarationBindings.get(scope);
        if (names == null) return List.of();
        List<Node> candidates = names.get(name);
        if (candidates == null) return List.of();
        return candidates.stream()
            .filter(node -> valueReference || List.of("class", "abstract_class", "interface", "type").contains(identities.get(node).get("family").getAsString()))
            .filter(node -> visibleBinding(node, scope, source)).toList();
    }

    private JsonObject unresolvedTarget(String reason) {
        JsonObject target = new JsonObject();
        target.addProperty("kind", "unresolved");
        target.addProperty("reason", reason);
        return record.targets.add(target);
    }

    private JsonObject resolveTarget(String reference, Node source, boolean valueReference) {
        int generic = reference.indexOf('<');
        String name = generic < 0 ? reference : reference.substring(0, generic);
        Node scope = bindingScope(source);
        String packageName = namespaceMembership.has("namespace_reference")
            ? namespaceMembership.get("namespace_reference").getAsString() : "";
        String[] parts = name.split("\\.");
        int first = 0;
        boolean memberLookup = parts[0].equals("this");
        if (memberLookup) {
            while (!(scope instanceof CompilationUnit) && !(scope instanceof TypeDeclaration<?>)
                && !(scope instanceof ObjectCreationExpr creation && creation.getAnonymousClassBody().isPresent())
                && !(scope instanceof EnumConstantDeclaration constant && !constant.getClassBody().isEmpty())) scope = bindingScope(scope);
            if (scope instanceof CompilationUnit || parts.length == 1) return unresolvedTarget("dynamic");
            first = 1;
        }
        int position = first;
        while (true) {
            if (valueReference && position < parts.length - 1 && shadowsReceiver(parts[position], scope, source)) return unresolvedTarget("dynamic");
            List<Node> matches = bindings(parts[position], scope, source, valueReference);
            if (matches.isEmpty() && position == 0 && scope instanceof CompilationUnit && !packageName.isEmpty() && name.startsWith(packageName + ".")) {
                position = packageName.split("\\.").length;
                continue;
            }
            if (matches.isEmpty() && position == first && !(scope instanceof CompilationUnit) && !memberLookup) {
                scope = bindingScope(scope);
                continue;
            }
            if (matches.size() != 1) return unresolvedTarget(matches.isEmpty() ? "external" : "ambiguous");
            scope = matches.get(0);
            position++;
            if (position == parts.length) {
                JsonObject target = new JsonObject();
                target.addProperty("kind", "resolved");
                target.add("declaration_id", identities.get(scope));
                return record.targets.add(target);
            }
        }
    }

    private int beginLine(Node node) {
        return sourceRange(node).begin.line;
    }

    private int beginColumn(Node node) {
        return sourceRange(node).begin.column;
    }

    private int endLine(Node node) {
        return sourceRange(node).end.line;
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

    private record BlockSpan(int startUtf8Offset, int endUtf8Offset) {}

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
