#!/usr/bin/env ruby
# frozen_string_literal: true

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

class NativeValueReference
  def initialize(document)
    @document = document
  end

  def fetch(key)
    @document.fetch(key)
  end

  def bind(index)
    @json = index.to_s.freeze
    freeze
  end

  def to_json(state = nil)
    @json
  end
end

class NativeValueTable
  def initialize
    @documents = []
    @references = []
  end

  def add(document)
    reference = NativeValueReference.new(document)
    @documents << document
    @references << reference
    reference
  end

  def encode(offset)
    @references.each_with_index { |reference, index| reference.bind(offset + index) }
    @documents
  end
end

class RubySourceExtractor
  EMPTY_ITEMS = [].freeze
  VISIBILITIES = %i[public protected private].freeze
  ATTRIBUTES = %i[attr_reader attr_writer attr_accessor].freeze
  COMPOSITION_KINDS = {include: "includes", prepend: "prepends", extend: "extends_singleton"}.freeze
  CALLABLE_FAMILIES = {"function" => "function", "callable_value" => "value", "anonymous" => "callable"}.freeze

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
    @texts = NativeValueTable.new
    @source_id_reference = @texts.add(source_id)
    @identities = NativeValueTable.new
    @identity_values = {}
    @targets = NativeValueTable.new
    @target_values = {}
    @declarations = []
    @namespaces = []
    @values = []
    @functions = []
    @callable_facts = []
    @relations = []
    @declaration_nodes = {}
    @declarations_by_qualified_name = {}
    @call_nodes = {}
    @loads = []
    @namespaces_by_owner = {}
    @targets_by_owner = Hash.new { |hash, owner| hash[owner] = {} }
    @empty_coverage = {}
    @types = NativeValueTable.new
    @absent_type = @types.add({"kind" => "absent"})
    @coverages = NativeValueTable.new
    @member_inventories = NativeValueTable.new
    @member_inventory_values = {}
    @namespace_memberships = NativeValueTable.new
    @placements = NativeValueTable.new
    @placements_by_scope = {}.compare_by_identity
    @assignments = NativeValueTable.new
    @unassigned = @assignments.add({"kind" => "unassigned", "expression" => "", "reference" => ""})
    @parameters = NativeValueTable.new
    @parameter_values = {}
    @unresolved_methods = []
    @limitations = Hash.new { |hash, key| hash[key] = [] }
  end

  def extract
    content = @path.read(encoding: "UTF-8")
    @content_digest = Digest::SHA256.hexdigest(content)
    @content_digest_reference = @texts.add(@content_digest)
    parsed = Prism.parse(content, filepath: @path.to_s)
    raise_parse_failure(parsed.errors.first) unless parsed.success?

    index_nodes(parsed.value, "", nil)
    collect_body(parsed.value.statements, "", nil, {"kind" => "file"}, nil, :unresolved)
    @relations.each do |item|
      source = item.fetch("source_declaration_id")
      item["target"] = resolve_reference(item.fetch("target_reference"), source.fetch("qualified_name"))
    end
    callable_values = []
    anonymous_callables = []
    @callable_facts.each do |fact|
      callable = fact.fetch("json")
      callable_values << callable if callable.fetch("kind") == "callable_value"
      anonymous_callables << callable if callable.fetch("kind") == "anonymous"
    end
    @declarations.each do |fact|
      fact["properties"] = fact.fetch("properties").values
      inventory = fact.fetch("inventory")
      fact["inventory"] = @member_inventory_values[inventory] ||= @member_inventories.add(inventory)
    end
    total_lines, code_lines = line_counts(content)
    {
      "imports" => imports,
      "exports" => [],
      "namespaces" => @namespaces,
      "declarations" => @declarations,
      "functions" => @functions,
      "values" => @values,
      "callable_values" => callable_values,
      "anonymous_callables" => anonymous_callables,
      "unresolved_methods" => @unresolved_methods,
      "inventory" => file_inventory,
      "calls" => calls,
      "declaration_relations" => @relations,
      "line_count" => total_lines,
      "code_line_count" => code_lines,
      "public_symbol_count" => public_symbol_count
    }
  end

  def record
    extracted = extract
    offset = 0
    tables = {"texts" => @texts, "identities" => @identities, "targets" => @targets, "types" => @types, "coverages" => @coverages,
              "member_inventories" => @member_inventories,
              "namespaces" => @namespace_memberships,
              "placements" => @placements, "assignments" => @assignments,
              "parameters" => @parameters}.transform_values do |table|
      documents = table.encode(offset)
      offset += documents.length
      documents
    end
    {"source_id" => @source_id, **tables, "facts" => extracted}
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

  def index_nodes(node, owner, calls)
    return if node.nil?

    nested_calls = calls
    body = nil
    body_calls = nil
    case node.type
    when :class_node, :module_node
      name = declaration_name(node.constant_path, owner)
      module_declaration = node.is_a?(Prism::ModuleNode)
      @declaration_nodes[node] = {
        "declaration_id" => identity(module_declaration ? "type" : "class", name, ordinal(node)),
        "kind" => module_declaration ? "module" : "class", "name" => name,
        "visibility" => "public", "visibility_intent" => "public", "declaration_annotations" => [],
        "line_count" => line_count(node.location.start_line, node.location.end_line), "methods" => [], "abstract_methods" => [], "properties" => {}, "signatures" => [],
        "inventory" => member_inventory
      }
      (@declarations_by_qualified_name[name] ||= []) << @declaration_nodes.fetch(node)
      owner = name
      nested_calls = nil
    when :call_node
      calls << node unless calls.nil?
      collect_import(node)
    when :def_node, :lambda_node, :block_node
      nested_calls = nil
      body = node.body
      body_calls = @call_nodes[node] = []
    end
    if body
      node.each_child_node do |child|
        index_nodes(child, owner, child.equal?(body) ? body_calls : nested_calls)
      end
    else
      node.each_child_node { |child| index_nodes(child, owner, nested_calls) }
    end
  end

  def collect_body(node, owner, declaration, lexical_scope, singleton_target, instance_member_kind)
    return if node.nil?

    if node.is_a?(Prism::StatementsNode)
      visibility = "public"
      node.body.each do |statement|
        visibility = collect_statement(statement, owner, declaration, lexical_scope, singleton_target, instance_member_kind, visibility)
      end
    else
      collect_statement(node, owner, declaration, lexical_scope, singleton_target, instance_member_kind, "public")
    end
  end

  def collect_statement(statement, owner, declaration, lexical_scope, singleton_target, instance_member_kind, visibility)
    case statement.type
    when :class_node, :module_node
      fact = @declaration_nodes.fetch(statement)
      name = fact.fetch("declaration_id").fetch("qualified_name")
      fact["placement"] = placement(lexical_scope, name.rpartition(".").first)
      @declarations << fact
      if statement.is_a?(Prism::ModuleNode)
        @namespaces << {"kind" => "module", "declaration_id" => identity("namespace", name, ordinal(statement)),
                       "placement" => fact.fetch("placement")}
      elsif statement.superclass
        @relations << relation(fact.fetch("declaration_id"), "extends", statement.superclass.slice)
      end
      collect_body(statement.body, name, fact, declaration_scope(fact.fetch("declaration_id")), nil, :static)
      return visibility
    when :def_node
      collect_callable(statement, owner, declaration, lexical_scope, singleton_target, visibility)
      return visibility
    when :singleton_class_node
      target = receiver_target(statement.expression, owner, declaration, singleton_target)
      container = lexical_scope.fetch("kind") == "block" ? lexical_scope.fetch("container") : lexical_scope
      block_scope = {"kind" => "block", "container" => container,
                     "start_utf8_offset" => statement.location.start_offset, "end_utf8_offset" => statement.location.end_offset}
      collect_body(statement.body, owner, target_declaration(target, declaration), block_scope, target, :unresolved)
      return visibility
    when :constant_write_node, :constant_path_write_node
      collect_constant(statement, owner, declaration, lexical_scope, singleton_target, instance_member_kind)
      return visibility
    when :local_variable_write_node
      collect_local_value(statement, owner, declaration, lexical_scope, singleton_target, instance_member_kind)
      return visibility
    when :instance_variable_write_node
      if declaration && instance_member_kind != :unresolved
        collect_property(statement.name.name, statement, declaration, lexical_scope, owner, instance_member_kind.to_s)
      else
        @limitations["values"] << limitation(statement, "unresolved_ownership", "Instance variable receiver has no exact source declaration.")
      end
      collect_body(statement.value, owner, declaration, lexical_scope, singleton_target, instance_member_kind)
      return visibility
    when :lambda_node, :block_node
      name = "<lambda@#{statement.location.start_offset}>"
      fact = callable_fact(statement, name, lexical_name(name, lexical_scope), "anonymous", visibility, lexical_scope, owner)
      @callable_facts << {"node" => statement, "json" => fact, "owner" => owner}
      collect_body(statement.body, owner, declaration, declaration_scope(fact.fetch("declaration_id")), singleton_target, instance_member_kind)
      return visibility
    when :call_node
      if statement.receiver.nil? && VISIBILITIES.include?(statement.name)
        names = symbol_arguments(statement)
        if names.empty?
          visibility = statement.name.name
        else
          apply_visibility(owner, names, statement.name.name, !singleton_target.nil?)
        end
        return visibility
      end
      if statement.receiver.nil? && ATTRIBUTES.include?(statement.name)
        unless declaration
          @limitations["values"] << limitation(statement, "unresolved_ownership", "Attribute receiver has no exact source declaration.")
          return visibility
        end
        arguments(statement).each do |argument|
          if argument.is_a?(Prism::SymbolNode) || argument.is_a?(Prism::StringNode)
            collect_property(argument.unescaped, argument, declaration, lexical_scope, owner, singleton_target ? "static" : "instance")
          else
            entry = declaration.fetch("inventory").fetch("properties")
            declaration.fetch("inventory")["properties"] = coverage(entry.fetch("limitations") + [limitation(statement, "dynamic_structure", "Attribute name requires runtime evaluation.")])
          end
        end
        return visibility
      end
      collect_composition(statement, declaration.fetch("declaration_id")) if declaration
    when :alias_method_node
      @limitations["unresolved_methods"] << limitation(statement, "unsupported_syntax", "Method alias binding is not represented.")
      declaration.fetch("inventory")["methods"] = coverage(@limitations["unresolved_methods"]) if declaration
    end
    statement.each_child_node { |child| collect_body(child, owner, declaration, lexical_scope, singleton_target, instance_member_kind) }
    visibility
  end

  def collect_callable(node, owner, declaration, lexical_scope, singleton_target, visibility)
    target = if node.receiver
               receiver_target(node.receiver, owner, declaration, singleton_target)
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
    name = node.name.name
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
      exact_owner = target_declaration(target, declaration)
      exact_owner.fetch("methods") << fact
      body_declaration = exact_owner
    else
      fact["receiver_reference"] = node.receiver ? node.receiver.slice : target_owner
      fact["owner"] = target
      @unresolved_methods << fact
    end
    @callable_facts << {"node" => node, "json" => fact, "owner" => target_owner}
    collect_body(node.body, target_owner, body_declaration, declaration_scope(fact.fetch("declaration_id")), nil, singleton ? :static : :instance)
  end

  def callable_fact(node, name, qualified_name, kind, visibility, lexical_scope, owner)
    family = CALLABLE_FAMILIES.fetch(kind, "method")
    location = node.location
    first_line = location.start_line
    last_line = location.end_line
    {"declaration_id" => identity(family, qualified_name, ordinal(node)), "source_id" => @source_id_reference,
     "name" => name, "qualified_name" => qualified_name, "kind" => kind,
     "visibility" => visibility, "visibility_intent" => visibility, "declaration_annotations" => [],
     "line_start" => first_line, "line_end" => last_line, "line_count" => line_count(first_line, last_line),
     "parameters" => parameters(node.parameters), "return_type" => absent_type, "decorators" => [], "docstring" => "",
     "placement" => placement(lexical_scope, owner)}
  end

  def collect_property(name, node, declaration, lexical_scope, owner, member_kind)
    properties = declaration.fetch("properties")
    key = [name, member_kind]
    return if properties.key?(key)

    owner_id = declaration.fetch("declaration_id")
    properties[key] = {"declaration_id" => identity("property", "#{owner_id.fetch("qualified_name")}.#{name}", ordinal(node)),
      "owner_declaration_id" => owner_id, "name" => name, "is_optional" => false, "type" => absent_type,
      "visibility" => "public", "member_kind" => member_kind, "placement" => placement(lexical_scope, owner),
      "assigned_values" => [@unassigned]}
  end

  def target_declaration(target, declaration)
    return nil unless target.fetch("kind") == "resolved"

    identity = target.fetch("declaration_id")
    return declaration if declaration && declaration.fetch("declaration_id").equal?(identity)

    @declarations_by_qualified_name.fetch(identity.fetch("qualified_name")).find { |item| item.fetch("declaration_id") == identity }
  end

  def receiver_target(receiver, owner, declaration, singleton_target)
    if self_receiver?(receiver)
      if singleton_target
        return singleton_target if singleton_target.fetch("kind") == "unresolved"

        return target_fact({"kind" => "unresolved", "reason" => "unobserved"})
      end
      return target_fact(declaration ? {"kind" => "resolved", "declaration_id" => declaration.fetch("declaration_id")} : {"kind" => "unresolved", "reason" => "dynamic"})
    end
    reference = constant_reference(receiver)
    reference.nil? ? target_fact({"kind" => "unresolved", "reason" => "dynamic"}) : resolve_reference(reference, owner)
  end

  def resolve_reference(reference, owner)
    targets = @targets_by_owner[owner]
    return targets.fetch(reference) if targets.key?(reference)

    targets[reference] = target_fact(reference_target(reference, owner))
  end

  def target_fact(document)
    @target_values[document] ||= @targets.add(document)
  end

  def reference_target(reference, owner)
    absolute = reference.start_with?("::")
    name = reference.sub(/\A::/, "").gsub("::", ".")
    prefix = absolute ? "" : owner
    loop do
      qualified = prefix.empty? ? name : "#{prefix}.#{name}"
      matches = @declarations_by_qualified_name[qualified]
      unless matches.nil?
        return {"kind" => "unresolved", "reason" => "ambiguous"} unless matches.length == 1

        return {"kind" => "resolved", "declaration_id" => matches.first.fetch("declaration_id")}
      end
      break if prefix.empty?

      separator = prefix.rindex(".")
      prefix = separator.nil? ? "" : prefix[0...separator]
    end
    {"kind" => "unresolved", "reason" => "external"}
  end

  def declaration_scope(identity)
    {"kind" => "declaration", "declaration_id" => identity}
  end

  def placement(scope, owner)
    owners = @placements_by_scope[scope] ||= {}
    owners.fetch(owner) do
      owners[owner] = @placements.add({"lexical_scope" => scope,
        "namespace" => @namespaces_by_owner[owner] ||= namespace_membership(owner)})
    end
  end

  def namespace_membership(owner)
    name = owner
    loop do
      cached = @namespaces_by_owner[name]
      return cached unless cached.nil?

      matches = @declarations_by_qualified_name.fetch(name, EMPTY_ITEMS).select { |item| item.fetch("kind") == "module" }
      unless matches.empty?
        target = matches.length == 1 ? {"kind" => "resolved", "declaration_id" => matches.first.fetch("declaration_id")} : {"kind" => "unresolved", "reason" => "ambiguous"}
        return @namespaces_by_owner[name] = @namespace_memberships.add(
          {"kind" => "member", "namespace_reference" => name, "target" => target_fact(target)})
      end
      separator = name.rindex(".")
      break if separator.nil?

      name = name[0...separator]
    end
    @namespaces_by_owner[""] ||= @namespace_memberships.add({"kind" => "none"})
  end

  def limitation(node, kind, description)
    {"kind" => kind, "location" => {"kind" => "source", "start_line" => node.location.start_line, "end_line" => node.location.end_line}, "description" => description}
  end

  def coverage(limitations, status = "complete")
    return @empty_coverage[status] ||= @coverages.add({"status" => status, "limitations" => EMPTY_ITEMS}) if limitations.empty?

    @coverages.add({"status" => "incomplete", "limitations" => limitations.dup})
  end

  def member_inventory
    {"methods" => coverage(EMPTY_ITEMS), "abstract_methods" => coverage(EMPTY_ITEMS, "not_applicable"),
     "properties" => coverage(EMPTY_ITEMS), "signatures" => coverage(EMPTY_ITEMS, "not_applicable")}
  end

  def file_inventory
    %w[declarations functions values callable_values anonymous_callables namespaces exports unresolved_methods].to_h do |kind|
      [kind, coverage(@limitations[kind], kind == "exports" ? "not_applicable" : "complete")]
    end
  end

  def parameters(node)
    return EMPTY_ITEMS if node.nil?

    node = node.parameters if node.is_a?(Prism::BlockParametersNode)
    return EMPTY_ITEMS if node.nil?
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
    key = [name, kind, has_default]
    @parameter_values.fetch(key) do
      @parameter_values[key] = @parameters.add({
        "name" => name, "type" => absent_type, "kind" => kind, "has_default" => has_default
      })
    end
  end

  def parameter_name(node)
    return "..." if node.is_a?(Prism::ForwardingParameterNode)
    return node.slice if node.is_a?(Prism::MultiTargetNode)

    name = node.name
    name.nil? ? node.slice : name.name
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
    return unless node.receiver.nil?

    kind = COMPOSITION_KINDS[node.name]
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

  def collect_local_value(node, owner, declaration, lexical_scope, singleton_target, instance_member_kind)
    name = node.name.name
    qualified = lexical_name(name, lexical_scope)
    if node.value.is_a?(Prism::LambdaNode)
      fact = callable_fact(node.value, name, qualified, "callable_value", "private", lexical_scope, owner)
      fact.merge!("declaration_kind" => "assignment", "value_kind" => "value_callable", "scope" => lexical_scope.fetch("kind") == "file" ? "module" : "local")
      @callable_facts << {"node" => node.value, "json" => fact, "owner" => owner}
      collect_body(node.value.body, owner, declaration, declaration_scope(fact.fetch("declaration_id")), singleton_target, instance_member_kind)
    else
      @values << {"declaration_id" => identity("value", qualified, ordinal(node)), "name" => name,
        "visibility" => "private", "visibility_intent" => "private", "line_count" => line_count(node.location.start_line, node.location.end_line),
        "declaration_kind" => "assignment", "value_kind" => LITERAL_NODES.include?(node.value.class) ? "value_literal" : "value_unknown",
        "scope" => lexical_scope.fetch("kind") == "file" ? "module" : "local", "placement" => placement(lexical_scope, owner)}
      collect_body(node.value, owner, declaration, lexical_scope, singleton_target, instance_member_kind)
    end
  end

  def collect_constant(node, owner, declaration, lexical_scope, singleton_target, instance_member_kind)
    name_node = node.is_a?(Prism::ConstantPathWriteNode) ? node.target : node
    name = declaration_name(name_node, owner)
    value = node.value
    value_kind = if value.is_a?(Prism::LambdaNode)
                   "value_callable"
                 elsif value.is_a?(Prism::ClassNode)
                   "value_class"
                 elsif LITERAL_NODES.include?(value.class)
                   "value_literal"
                 else
                   "value_unknown"
                 end
    if value.is_a?(Prism::LambdaNode)
      collect_callable_constant(node, value, name, lexical_scope, owner, declaration, singleton_target, instance_member_kind)
      return
    end
    @values << {
      "declaration_id" => identity("value", name, ordinal(node)),
      "name" => name,
      "visibility" => "public",
      "visibility_intent" => "public",
      "line_count" => line_count(node.location.start_line, node.location.end_line),
      "declaration_kind" => "constant",
      "value_kind" => value_kind,
      "scope" => constant_scope(owner),
      "placement" => placement(lexical_scope, owner)
    }
    collect_body(value, owner, nil, lexical_scope, nil, :unresolved)
  end

  def collect_callable_constant(node, value, name, lexical_scope, owner, declaration, singleton_target, instance_member_kind)
    fact = callable_fact(value, name, name, "callable_value", "public", lexical_scope, owner)
    fact["declaration_id"] = identity("value", name, ordinal(node))
    fact.merge!("declaration_kind" => "constant", "value_kind" => "value_callable",
                "scope" => constant_scope(owner))
    @callable_facts << {"node" => value, "json" => fact, "owner" => owner}
    collect_body(value.body, owner, declaration, declaration_scope(fact.fetch("declaration_id")), singleton_target, instance_member_kind)
  end

  def constant_scope(owner)
    owner.empty? ? "module" : "member"
  end

  def collect_import(node)
    return unless node.receiver.nil?
    return unless node.name == :require || node.name == :require_relative

    items = arguments(node)
    return unless items.length == 1 && items.first.is_a?(Prism::StringNode)

    specifier = items.first.unescaped
    relative = node.name == :require_relative
    normalized = normalized_import(specifier, relative)
    @loads << {
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

  def imports
    @loads.sort_by { |load| load.fetch("location") }.each_with_index.map do |load, index|
      load.delete("location")
      load.merge("statement_id" => index + 1)
    end
  end

  def normalized_import(specifier, relative)
    normalized = if relative
                   @relative_directory ||= @path.relative_path_from(@root).dirname
                   @relative_directory.join(specifier).cleanpath.to_s
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
      source_identity = source.fetch("json").fetch("declaration_id")
      owner = source.fetch("owner")
      ordinal = 0
      @call_nodes.fetch(source.fetch("node")).each do |node|
        ordinal += 1
        target = call_target(node, owner)
        candidates = facts_by_qualified_name[target]
        resolved = candidates && candidates.length == 1 ? candidates.first.fetch("json").fetch("declaration_id") : nil
        resolution = if target.nil?
                       "dynamic"
                     elsif resolved
                       "resolved"
                     else
                       "unresolved"
                     end
        fact = {
          "source_callable_id" => source_identity,
          "ordinal" => ordinal,
          "target_callable_id" => resolved,
          "source_id" => @source_id_reference,
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
    name = node.name.name
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

    node.name.name
  end

  def arguments(node)
    node.arguments.nil? ? EMPTY_ITEMS : node.arguments.arguments
  end

  def symbol_arguments(node)
    arguments(node).filter_map do |argument|
      argument.unescaped if argument.is_a?(Prism::SymbolNode)
    end
  end

  def self_receiver?(node)
    receiver_expression(node).is_a?(Prism::SelfNode)
  end

  def receiver_expression(node)
    while node.is_a?(Prism::ParenthesesNode)
      node = node.body
      if node.is_a?(Prism::StatementsNode)
        return nil unless node.body.length == 1

        node = node.body.first
      end
    end
    node
  end

  def constant_reference(node)
    node = receiver_expression(node)
    return nil unless node.is_a?(Prism::ConstantReadNode) || node.is_a?(Prism::ConstantPathNode)

    node.full_name
  rescue Prism::ConstantPathNode::DynamicPartsInConstantPathError,
         Prism::ConstantPathNode::MissingNodesInConstantPathError
    nil
  end

  def declaration_name(node, owner)
    raw = if node.is_a?(Prism::ConstantWriteNode)
            node.name.name
          else
            constant_reference(node) || node.slice
          end
    absolute = raw.start_with?("::")
    normalized = raw.sub(/\A::/, "").gsub("::", ".")
    if !absolute && !owner.empty?
      if normalized.include?(".")
        qualifier, _, name = normalized.rpartition(".")
        target = reference_target(qualifier, owner)
        return "#{target.fetch("declaration_id").fetch("qualified_name")}.#{name}" if target.fetch("kind") == "resolved"

        return normalized
      end
      "#{owner}.#{normalized}"
    else
      normalized
    end
  end

  def identity(family, name, ordinal)
    key = [family, name, ordinal]
    @identity_values.fetch(key) do
      @identity_values[key] = @identities.add({"source_id" => @source_id_reference, "family" => family,
        "qualified_name" => name, "ordinal" => ordinal, "content_digest" => @content_digest_reference})
    end
  end

  def absent_type
    @absent_type
  end

  def relation(identity, kind, target)
    {"source_declaration_id" => identity, "kind" => kind, "target_reference" => target}
  end

  def ordinal(node)
    node.location.start_offset + 1
  end

  def line_count(first_line, last_line)
    count = last_line - first_line + 1
    count < 1 ? 1 : count
  end

  def line_counts(content)
    carriage_returns = content.count("\r")
    total = 1 + content.count("\n") + carriage_returns
    total -= content.scan("\r\n").length unless carriage_returns.zero?
    in_block_comment = false
    code = content.each_line.count do |line|
      line.lstrip!
      if in_block_comment
        in_block_comment = false if line.start_with?("=end")
        false
      elsif line.start_with?("=begin")
        in_block_comment = true
        false
      else
        !line.empty? && !line.start_with?("#")
      end
    end
    [total, code]
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
    input = JSON.parse($stdin.read)
    raise ArgumentError, "Expected a JSON object mapping source ids to Ruby file paths." unless input.is_a?(Hash)

    input.each do |source_id, path|
      unless source_id.is_a?(String) && path.is_a?(String)
        raise ArgumentError, "Expected source ids and paths to be strings."
      end

      record = RubySourceExtractor.new(root, path, source_id).record
      puts JSON.generate(record)
      $stdout.flush
    end
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
