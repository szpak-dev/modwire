#!/usr/bin/env ruby

require "json"
require "pathname"
require "prism"
require "digest"

class SourceParseFailure < StandardError
  attr_reader :document

  def initialize(path, line, column, diagnostic)
    super(diagnostic)
    @document = {
      "code" => "source_parse",
      "language" => "ruby",
      "path" => path,
      "line" => line,
      "column" => column,
      "diagnostic" => diagnostic
    }
  end
end

class RubySourceExtractor
  LITERAL_NODES = [
    Prism::ArrayNode,
    Prism::FalseNode,
    Prism::FloatNode,
    Prism::HashNode,
    Prism::ImaginaryNode,
    Prism::IntegerNode,
    Prism::NilNode,
    Prism::RangeNode,
    Prism::RationalNode,
    Prism::StringNode,
    Prism::SymbolNode,
    Prism::TrueNode
  ].freeze

  def initialize(root, path, source_id)
    @root = Pathname.new(root).expand_path
    @path = Pathname.new(path).expand_path
    @source_id = source_id
    @declarations = []
    @namespaces = []
    @values = []
    @functions = []
    @callable_facts = []
    @relations = []
    @declaration_nodes = {}
    @unresolved_methods = []
    @limitations = Hash.new { |hash, key| hash[key] = [] }
  end

  def extract
    content = @path.read(encoding: "UTF-8")
    @content_digest = Digest::SHA256.hexdigest(content)
    parsed = Prism.parse(content, filepath: @path.to_s)
    raise_parse_failure(parsed.errors.first) unless parsed.success?

    index_declarations(parsed.value, "")
    @declarations_by_qualified_name = @declaration_nodes.values.group_by do |declaration|
      declaration.fetch("declaration_id").fetch("qualified_name")
    end
    collect_body(parsed.value.statements, "", nil, {"kind" => "file"}, nil)
    @relations.each do |item|
      source = item.fetch("source_declaration_id")
      item["target"] = resolve_reference(item.fetch("target_reference"), source.fetch("qualified_name"))
    end
    callable_values = @callable_facts
                      .map { |fact| fact.fetch("json") }
                      .select { |callable| callable.fetch("kind") == "callable_value" }
    {
      "imports" => imports(parsed.value),
      "exports" => [],
      "namespaces" => @namespaces,
      "declarations" => @declarations,
      "functions" => @functions,
      "values" => @values,
      "callable_values" => callable_values,
      "anonymous_callables" => @callable_facts.map { |fact| fact.fetch("json") }.select { |fact| fact.fetch("kind") == "anonymous" },
      "unresolved_methods" => @unresolved_methods,
      "inventory" => file_inventory,
      "calls" => calls,
      "declaration_relations" => @relations,
      "line_count" => [1, content.split(/\r\n|\n|\r/, -1).length].max,
      "code_line_count" => code_line_count(content),
      "public_symbol_count" => public_symbol_count
    }
  end

  private

  def raise_parse_failure(error)
    location = error.location
    raise SourceParseFailure.new(
      @path.to_s,
      location.start_line,
      location.start_column + 1,
      error.message
    )
  end

  def index_declarations(node, owner)
    return if node.nil?

    if node.is_a?(Prism::ClassNode) || node.is_a?(Prism::ModuleNode)
      name = declaration_name(node.constant_path, owner)
      module_declaration = node.is_a?(Prism::ModuleNode)
      @declaration_nodes[node] = {
        "declaration_id" => identity(module_declaration ? "type" : "class", name, ordinal(node)),
        "kind" => module_declaration ? "module" : "class", "name" => name,
        "visibility" => "public", "visibility_intent" => "public", "declaration_annotations" => [],
        "line_count" => line_count(node), "methods" => [], "abstract_methods" => [], "properties" => [], "signatures" => [],
        "inventory" => member_inventory
      }
      owner = name
    end
    node.child_nodes.compact.each { |child| index_declarations(child, owner) }
  end

  def collect_body(node, owner, declaration, lexical_scope, singleton_target)
    return if node.nil?

    visibility = "public"
    statements = node.is_a?(Prism::StatementsNode) ? node.body : [node]
    statements.each do |statement|
      if statement.is_a?(Prism::ClassNode) || statement.is_a?(Prism::ModuleNode)
        fact = @declaration_nodes.fetch(statement)
        fact["placement"] = placement(lexical_scope, owner)
        @declarations << fact
        name = fact.fetch("declaration_id").fetch("qualified_name")
        if statement.is_a?(Prism::ModuleNode)
          @namespaces << {"kind" => "module", "declaration_id" => identity("namespace", name, ordinal(statement)),
                         "placement" => placement(lexical_scope, owner)}
        elsif statement.superclass
          @relations << relation(fact.fetch("declaration_id"), "extends", statement.superclass.slice)
        end
        collect_body(statement.body, name, fact, declaration_scope(fact.fetch("declaration_id")), nil)
      elsif statement.is_a?(Prism::DefNode)
        collect_callable(statement, owner, declaration, lexical_scope, singleton_target, visibility)
      elsif statement.is_a?(Prism::SingletonClassNode)
        target = receiver_target(statement.expression, owner, declaration)
        container = lexical_scope.fetch("kind") == "block" ? lexical_scope.fetch("container") : lexical_scope
        block_scope = {"kind" => "block", "container" => container,
                       "start_utf8_offset" => statement.location.start_offset, "end_utf8_offset" => statement.location.end_offset}
        collect_body(statement.body, owner, declaration, block_scope, target)
      elsif constant_write?(statement)
        collect_constant(statement, owner, lexical_scope)
      elsif statement.is_a?(Prism::LocalVariableWriteNode)
        collect_local_value(statement, owner, declaration, lexical_scope)
      elsif statement.is_a?(Prism::InstanceVariableWriteNode)
        if declaration
          collect_property(statement.name.to_s, statement, declaration, lexical_scope, owner)
        else
          @limitations["values"] << limitation(statement, "unresolved_ownership", "Instance variable receiver has no exact source declaration.")
        end
        collect_body(statement.value, owner, declaration, lexical_scope, singleton_target)
      elsif statement.is_a?(Prism::LambdaNode) || statement.is_a?(Prism::BlockNode)
        name = "<lambda@#{statement.location.start_offset}>"
        fact = callable_fact(statement, name, lexical_name(name, lexical_scope), "anonymous", visibility, lexical_scope, owner)
        @callable_facts << {"node" => statement, "json" => fact, "owner" => owner}
        collect_body(statement.body, owner, declaration, declaration_scope(fact.fetch("declaration_id")), nil)
      elsif visibility_call?(statement)
        names = symbol_arguments(statement)
        if names.empty?
          visibility = statement.name.to_s
        else
          apply_visibility(owner, names, statement.name.to_s, !singleton_target.nil?)
        end
      elsif statement.is_a?(Prism::CallNode) && statement.receiver.nil? && [:attr_reader, :attr_writer, :attr_accessor].include?(statement.name) && declaration
        arguments(statement).each do |argument|
          if argument.is_a?(Prism::SymbolNode) || argument.is_a?(Prism::StringNode)
            collect_property(argument.unescaped, argument, declaration, lexical_scope, owner)
          else
            entry = declaration.fetch("inventory").fetch("properties")
            declaration.fetch("inventory")["properties"] = coverage(entry.fetch("limitations") + [limitation(statement, "dynamic_structure", "Attribute name requires runtime evaluation.")])
          end
        end
      else
        collect_composition(statement, declaration.fetch("declaration_id")) if declaration
        if statement.is_a?(Prism::AliasMethodNode)
          @limitations["unresolved_methods"] << limitation(statement, "unsupported_syntax", "Method alias binding is not represented.")
          declaration.fetch("inventory")["methods"] = coverage(@limitations["unresolved_methods"]) if declaration
        end
        statement.child_nodes.compact.each { |child| collect_body(child, owner, declaration, lexical_scope, singleton_target) }
      end
    end
  end

  def collect_callable(node, owner, declaration, lexical_scope, singleton_target, visibility)
    target = if node.receiver
               receiver_target(node.receiver, owner, declaration)
             elsif singleton_target
               singleton_target
             elsif declaration
               {"kind" => "resolved", "declaration_id" => declaration.fetch("declaration_id")}
             else
               nil
             end
    singleton = !node.receiver.nil? || !singleton_target.nil?
    kind = if target.nil?
             "function"
           elsif singleton
             "type_method"
           elsif node.name == :initialize
             "constructor"
           else
             "instance_method"
           end
    name = node.name.to_s
    target_owner = if target && target.fetch("kind") == "resolved"
                     target.fetch("declaration_id").fetch("qualified_name")
                   elsif target
                     node.receiver ? node.receiver.slice : "<singleton@#{node.location.start_offset}>"
                   else
                     owner
                   end
    qualified = target_owner.empty? ? name : "#{target_owner}.#{name}"
    fact = callable_fact(node, name, qualified, kind, node.receiver ? "public" : visibility, lexical_scope, owner)
    body_declaration = nil
    if target.nil?
      @functions << fact
    elsif target.fetch("kind") == "resolved"
      fact["owner_declaration_id"] = target.fetch("declaration_id")
      exact_owner = @declaration_nodes.values.find { |item| item.fetch("declaration_id") == target.fetch("declaration_id") }
      exact_owner.fetch("methods") << fact
      body_declaration = exact_owner
    else
      fact["receiver_reference"] = node.receiver ? node.receiver.slice : target_owner
      fact["owner"] = target
      @unresolved_methods << fact
    end
    @callable_facts << {"node" => node, "json" => fact, "owner" => target_owner}
    collect_body(node.body, target_owner, body_declaration, declaration_scope(fact.fetch("declaration_id")), nil)
  end

  def callable_fact(node, name, qualified_name, kind, visibility, lexical_scope, owner)
    family = {"function" => "function", "callable_value" => "value", "anonymous" => "callable"}.fetch(kind, "method")
    {"declaration_id" => identity(family, qualified_name, ordinal(node)), "source_id" => @source_id,
     "name" => name, "qualified_name" => qualified_name, "kind" => kind,
     "visibility" => visibility, "visibility_intent" => visibility, "declaration_annotations" => [],
     "line_start" => node.location.start_line, "line_end" => node.location.end_line, "line_count" => line_count(node),
     "parameters" => parameters(node.parameters), "return_type" => absent_type, "decorators" => [], "docstring" => "",
     "placement" => placement(lexical_scope, owner)}
  end

  def collect_property(name, node, declaration, lexical_scope, owner)
    properties = declaration.fetch("properties")
    return if properties.any? { |item| item.fetch("name") == name }

    owner_id = declaration.fetch("declaration_id")
    properties << {"declaration_id" => identity("property", "#{owner_id.fetch("qualified_name")}.#{name}", ordinal(node)),
      "owner_declaration_id" => owner_id, "name" => name, "is_optional" => false, "type" => absent_type,
      "visibility" => "public", "member_kind" => "instance", "placement" => placement(lexical_scope, owner),
      "assigned_values" => [{"kind" => "unassigned", "expression" => "", "reference" => ""}]}
  end

  def receiver_target(receiver, owner, declaration)
    if self_receiver?(receiver)
      return declaration ? {"kind" => "resolved", "declaration_id" => declaration.fetch("declaration_id")} : {"kind" => "unresolved", "reason" => "dynamic"}
    end
    reference = constant_reference(receiver)
    reference.nil? ? {"kind" => "unresolved", "reason" => "dynamic"} : resolve_reference(reference, owner)
  end

  def resolve_reference(reference, owner)
    absolute = reference.start_with?("::")
    name = reference.sub(/\A::/, "").gsub("::", ".")
    owner_parts = owner.split(".")
    prefixes = absolute ? [""] : owner_parts.length.downto(0).map { |length| owner_parts.take(length).join(".") }
    prefixes.each do |prefix|
      qualified = prefix.empty? ? name : "#{prefix}.#{name}"
      matches = @declarations_by_qualified_name.fetch(qualified, [])
      next if matches.empty?
      return {"kind" => "unresolved", "reason" => "ambiguous"} unless matches.length == 1

      return {"kind" => "resolved", "declaration_id" => matches.first.fetch("declaration_id")}
    end
    {"kind" => "unresolved", "reason" => "external"}
  end

  def declaration_scope(identity)
    {"kind" => "declaration", "declaration_id" => identity}
  end

  def placement(scope, owner)
    name = owner
    namespace = {"kind" => "none"}
    loop do
      matches = @declarations_by_qualified_name.fetch(name, []).select { |item| item.fetch("kind") == "module" }
      unless matches.empty?
        target = matches.length == 1 ? {"kind" => "resolved", "declaration_id" => matches.first.fetch("declaration_id")} : {"kind" => "unresolved", "reason" => "ambiguous"}
        namespace = {"kind" => "member", "namespace_reference" => name, "target" => target}
        break
      end
      separator = name.rindex(".")
      break if separator.nil?

      name = name[0...separator]
    end
    {"lexical_scope" => scope, "namespace" => namespace}
  end

  def limitation(node, kind, description)
    {"kind" => kind, "location" => {"kind" => "source", "start_line" => node.location.start_line, "end_line" => node.location.end_line}, "description" => description}
  end

  def coverage(limitations, status = "complete")
    {"status" => limitations.empty? ? status : "incomplete", "limitations" => limitations.dup}
  end

  def member_inventory
    {"methods" => coverage([]), "abstract_methods" => coverage([], "not_applicable"),
     "properties" => coverage([]), "signatures" => coverage([], "not_applicable")}
  end

  def file_inventory
    %w[declarations functions values callable_values anonymous_callables namespaces exports unresolved_methods].to_h do |kind|
      [kind, coverage(@limitations[kind], kind == "exports" ? "not_applicable" : "complete")]
    end
  end

  def parameters(node)
    return [] if node.nil?

    node = node.parameters if node.is_a?(Prism::BlockParametersNode)
    return [] if node.nil?
    return (1..node.maximum).map { |index| parameter_fact("_#{index}", "positional", false) } if node.is_a?(Prism::NumberedParametersNode)
    return [parameter_fact("it", "positional", false)] if node.is_a?(Prism::ItParametersNode)

    result = []
    node.requireds.each { |parameter| result << parameter_fact(parameter_name(parameter), "positional", false) }
    node.optionals.each { |parameter| result << parameter_fact(parameter_name(parameter), "positional", true) }
    result << parameter_fact(parameter_name(node.rest), "variadic_positional", false) if node.rest
    node.posts.each { |parameter| result << parameter_fact(parameter_name(parameter), parameter_kind(parameter), false) }
    node.keywords.each do |parameter|
      result << parameter_fact(parameter_name(parameter), "named_only", parameter.is_a?(Prism::OptionalKeywordParameterNode))
    end
    result << parameter_fact(parameter_name(node.keyword_rest), parameter_kind(node.keyword_rest), false) if node.keyword_rest
    result << parameter_fact(parameter_name(node.block), "named_only", false) if node.block
    result
  end

  def parameter_fact(name, kind, has_default)
    {
      "name" => name,
      "type" => absent_type,
      "kind" => kind,
      "has_default" => has_default
    }
  end

  def parameter_name(node)
    return "..." if node.is_a?(Prism::ForwardingParameterNode)
    return node.slice if node.is_a?(Prism::MultiTargetNode)

    name = node.name
    name.nil? ? node.slice : name.to_s
  end

  def parameter_kind(node)
    if node.is_a?(Prism::KeywordRestParameterNode)
      "variadic_named"
    elsif node.is_a?(Prism::ForwardingParameterNode)
      "variadic_positional"
    else
      "positional"
    end
  end

  def apply_visibility(owner, names, visibility, singleton)
    @callable_facts.each do |fact|
      callable = fact.fetch("json")
      next unless fact.fetch("owner") == owner && names.include?(callable.fetch("name"))
      instance_callable = callable.fetch("kind") == "instance_method" || callable.fetch("kind") == "constructor"
      type_callable = callable.fetch("kind") == "type_method"
      next unless singleton ? type_callable : instance_callable

      callable["visibility"] = visibility
      callable["visibility_intent"] = visibility
    end
  end

  def collect_composition(node, declaration_id)
    return unless node.is_a?(Prism::CallNode) && node.receiver.nil?

    kind = {include: "includes", prepend: "prepends", extend: "extends_singleton"}[node.name]
    return if kind.nil?

    arguments(node).each do |argument|
      reference = constant_reference(argument)
      @relations << relation(declaration_id, kind, reference) unless reference.nil?
    end
  end

  def lexical_name(name, scope)
    container = scope.fetch("kind") == "block" ? scope.fetch("container") : scope
    container.fetch("kind") == "file" ? name : "#{container.fetch("declaration_id").fetch("qualified_name")}.#{name}"
  end

  def collect_local_value(node, owner, declaration, lexical_scope)
    name = node.name.to_s
    qualified = lexical_name(name, lexical_scope)
    if node.value.is_a?(Prism::LambdaNode)
      fact = callable_fact(node.value, name, qualified, "callable_value", "private", lexical_scope, owner)
      fact.merge!("declaration_kind" => "assignment", "value_kind" => "value_callable", "scope" => lexical_scope.fetch("kind") == "file" ? "module" : "local")
      @callable_facts << {"node" => node.value, "json" => fact, "owner" => owner}
      collect_body(node.value.body, owner, declaration, declaration_scope(fact.fetch("declaration_id")), nil)
    else
      @values << {"declaration_id" => identity("value", qualified, ordinal(node)), "name" => name,
        "visibility" => "private", "visibility_intent" => "private", "line_count" => line_count(node),
        "declaration_kind" => "assignment", "value_kind" => LITERAL_NODES.any? { |type| node.value.is_a?(type) } ? "value_literal" : "value_unknown",
        "scope" => lexical_scope.fetch("kind") == "file" ? "module" : "local", "placement" => placement(lexical_scope, owner)}
      collect_body(node.value, owner, declaration, lexical_scope, nil)
    end
  end

  def collect_constant(node, owner, lexical_scope)
    name_node = node.is_a?(Prism::ConstantPathWriteNode) ? node.target : node
    name = declaration_name(name_node, owner)
    value = node.value
    value_kind = if value.is_a?(Prism::LambdaNode)
                   "value_callable"
                 elsif value.is_a?(Prism::ClassNode)
                   "value_class"
                 elsif LITERAL_NODES.any? { |type| value.is_a?(type) }
                   "value_literal"
                 else
                   "value_unknown"
                 end
    if value.is_a?(Prism::LambdaNode)
      collect_callable_constant(node, value, name, lexical_scope, owner)
      return
    end
    @values << {
      "declaration_id" => identity("value", name, ordinal(node)),
      "name" => name,
      "visibility" => "public",
      "visibility_intent" => "public",
      "line_count" => line_count(node),
      "declaration_kind" => "constant",
      "value_kind" => value_kind,
      "scope" => lexical_scope.fetch("kind") == "file" ? "module" : "local",
      "placement" => placement(lexical_scope, owner)
    }
    collect_body(value, owner, nil, lexical_scope, nil)
  end

  def collect_callable_constant(node, value, name, lexical_scope, owner)
    fact = callable_fact(value, name, name, "callable_value", "public", lexical_scope, owner)
    fact["declaration_id"] = identity("value", name, ordinal(node))
    fact.merge!("declaration_kind" => "constant", "value_kind" => "value_callable",
                "scope" => lexical_scope.fetch("kind") == "file" ? "module" : "local")
    @callable_facts << {"node" => value, "json" => fact, "owner" => owner}
    collect_body(value.body, owner, nil, declaration_scope(fact.fetch("declaration_id")), nil)
  end

  def imports(program)
    loads = []
    walk(program) do |node|
      next unless node.is_a?(Prism::CallNode) && node.receiver.nil?
      next unless node.name == :require || node.name == :require_relative

      items = arguments(node)
      next unless items.length == 1 && items.first.is_a?(Prism::StringNode)

      specifier = items.first.unescaped
      relative = node.name == :require_relative
      normalized = normalized_import(specifier, relative)
      loads << {
        "location" => node.location.start_offset,
        "path" => specifier,
        "is_relative" => relative,
        "normalized_path" => normalized,
        "imported_name" => File.basename(normalized),
        "is_aliased" => false,
        "crossing_type" => "module",
        "file_barrier_crossed" => true,
        "join_key" => normalized,
        "uses_joined_import" => false,
        "imported_symbols" => []
      }
    end
    loads.sort_by { |load| load.fetch("location") }.each_with_index.map do |load, index|
      load.delete("location")
      load.merge("statement_id" => index + 1)
    end
  end

  def normalized_import(specifier, relative)
    normalized = if relative
                   source = @path.relative_path_from(@root)
                   Pathname.new(source.dirname).join(specifier).cleanpath.to_s
                 else
                   specifier
                 end
    normalized.sub(/\.rb\z/, "").sub(%r{\A/+}, "")
  end

  def calls
    facts_by_qualified_name = @callable_facts.group_by do |fact|
      fact.fetch("json").fetch("qualified_name")
    end
    result = []
    @callable_facts.each do |source|
      callable = source.fetch("json")
      ordinal = 0
      walk(source.fetch("node").body, stop_at_definitions: true) do |node|
        next unless node.is_a?(Prism::CallNode)

        ordinal += 1
        target = call_target(node, source.fetch("owner"))
        candidates = target.nil? ? [] : facts_by_qualified_name.fetch(target, [])
        resolution = if target.nil?
                       "dynamic"
                     elsif candidates.length == 1
                       "resolved"
                     else
                       "unresolved"
                     end
        fact = {
          "source_callable_id" => callable.fetch("declaration_id"),
          "ordinal" => ordinal,
          "target_callable_id" => candidates.length == 1 ? candidates.first.fetch("json").fetch("declaration_id") : nil,
          "source_id" => @source_id,
          "line" => node.location.start_line,
          "expression" => node.slice,
          "resolution" => resolution,
          "target_name" => call_name(node)
        }
        result << fact
      end
    end
    result
  end

  def call_target(node, owner)
    name = node.name.to_s
    if node.receiver.nil? || self_receiver?(node.receiver)
      return name if owner.empty?

      return "#{owner}.#{name}"
    end

    receiver = constant_reference(node.receiver)
    return nil if receiver.nil?

    target = resolve_reference(receiver, owner)
    return nil unless target.fetch("kind") == "resolved"
    normalized = target.fetch("declaration_id").fetch("qualified_name")
    name == "new" ? "#{normalized}.initialize" : "#{normalized}.#{name}"
  end

  def call_name(node)
    if node.name == :new
      receiver = constant_reference(node.receiver)
      return receiver.sub(/\A::/, "").gsub("::", ".") unless receiver.nil?
    end

    node.name.to_s
  end

  def walk(node, stop_at_definitions: false, &block)
    return if node.nil?

    yield node
    node.child_nodes.compact.each do |child|
      next if stop_at_definitions && (child.is_a?(Prism::DefNode) || child.is_a?(Prism::LambdaNode) || child.is_a?(Prism::BlockNode) || child.is_a?(Prism::ClassNode) || child.is_a?(Prism::ModuleNode))

      walk(child, stop_at_definitions: stop_at_definitions, &block)
    end
  end

  def arguments(node)
    node.arguments.nil? ? [] : node.arguments.arguments
  end

  def symbol_arguments(node)
    arguments(node).filter_map do |argument|
      argument.unescaped if argument.is_a?(Prism::SymbolNode)
    end
  end

  def visibility_call?(node)
    node.is_a?(Prism::CallNode) && node.receiver.nil? && [:public, :protected, :private].include?(node.name)
  end

  def self_receiver?(node)
    node.is_a?(Prism::SelfNode)
  end

  def constant_write?(node)
    node.is_a?(Prism::ConstantWriteNode) || node.is_a?(Prism::ConstantPathWriteNode)
  end

  def constant_reference(node)
    return nil unless node.is_a?(Prism::ConstantReadNode) || node.is_a?(Prism::ConstantPathNode)

    node.full_name
  rescue Prism::ConstantPathNode::DynamicPartsInConstantPathError,
         Prism::ConstantPathNode::MissingNodesInConstantPathError
    nil
  end

  def declaration_name(node, owner)
    raw = if node.is_a?(Prism::ConstantWriteNode)
            node.name.to_s
          else
            constant_reference(node) || node.slice
          end
    absolute = raw.start_with?("::")
    normalized = raw.sub(/\A::/, "").gsub("::", ".")
    if !absolute && !owner.empty? && !normalized.include?(".")
      "#{owner}.#{normalized}"
    else
      normalized
    end
  end

  def identity(family, name, ordinal)
    {"source_id" => @source_id, "family" => family, "qualified_name" => name, "ordinal" => ordinal, "content_digest" => @content_digest}
  end

  def absent_type
    {"kind" => "absent"}
  end

  def relation(identity, kind, target)
    {"source_declaration_id" => identity.dup, "kind" => kind, "target_reference" => target}
  end

  def ordinal(node)
    node.location.start_offset + 1
  end

  def line_count(node)
    [1, node.location.end_line - node.location.start_line + 1].max
  end

  def code_line_count(content)
    in_block_comment = false
    content.each_line.count do |line|
      stripped = line.strip
      if in_block_comment
        in_block_comment = false if stripped.start_with?("=end")
        false
      elsif stripped.start_with?("=begin")
        in_block_comment = true
        false
      else
        !stripped.empty? && !stripped.start_with?("#")
      end
    end
  end

  def public_symbol_count
    declarations = @declarations.count { |declaration| declaration.fetch("visibility") == "public" }
    functions = @functions.count { |function| function.fetch("visibility") == "public" }
    values = @values.count { |value| value.fetch("visibility") == "public" }
    declarations + functions + values
  end
end

class Script
  def execute(arguments)
    unless arguments.length >= 2 && arguments[0] == "--batch"
      raise ArgumentError, "Expected --batch followed by the Ruby source root."
    end

    root = arguments[1]
    json_lines = arguments.include?("--jsonl")
    input = JSON.parse($stdin.read)
    raise ArgumentError, "Expected a JSON object mapping source ids to Ruby file paths." unless input.is_a?(Hash)

    result = {}
    input.each do |source_id, path|
      unless source_id.is_a?(String) && path.is_a?(String)
        raise ArgumentError, "Expected source ids and paths to be strings."
      end

      extracted = RubySourceExtractor.new(root, path, source_id).extract
      if json_lines
        puts JSON.generate([source_id, extracted])
      else
        result[source_id] = extracted
      end
    end
    puts JSON.generate(result) unless json_lines
    0
  rescue SourceParseFailure => error
    warn "modwire-error:#{JSON.generate(error.document)}"
    1
  rescue StandardError => error
    warn error.message
    1
  end
end

exit Script.new.execute(ARGV)
