#!/usr/bin/env ruby

require "json"
require "pathname"
require "prism"

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
    @callable_facts = []
    @relations = []
  end

  def extract
    content = @path.read(encoding: "UTF-8")
    parsed = Prism.parse(content, filepath: @path.to_s)
    raise_parse_failure(parsed.errors.first) unless parsed.success?

    collect_body(parsed.value.statements, "", nil, false)
    callables = @callable_facts.map { |fact| fact.fetch("json") }
    {
      "imports" => imports(parsed.value),
      "exports" => [],
      "namespaces" => @namespaces,
      "declarations" => @declarations,
      "functions" => [],
      "values" => @values,
      "callables" => callables,
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

  def collect_body(statements, owner, declaration, singleton)
    return if statements.nil?

    visibility = "public"
    statement_sequence(statements).each do |node|
      if node.is_a?(Prism::ClassNode) || node.is_a?(Prism::ModuleNode)
        collect_declaration(node, owner)
      elsif node.is_a?(Prism::DefNode) && !owner.empty?
        collect_method(node, owner, declaration, visibility, singleton)
      elsif node.is_a?(Prism::SingletonClassNode) && self_receiver?(node.expression)
        collect_body(node.body, owner, declaration, true)
      elsif constant_write?(node)
        collect_constant(node, owner)
      elsif visibility_call?(node)
        names = symbol_arguments(node)
        if names.empty?
          visibility = node.name.to_s
        else
          apply_visibility(owner, names, node.name.to_s, singleton)
        end
      elsif declaration
        collect_composition(node, declaration.fetch("declaration_id"))
      end
    end
  end

  def statement_sequence(node)
    if node.is_a?(Prism::StatementsNode)
      node.body
    elsif node.is_a?(Prism::BeginNode)
      node.statements.nil? ? [] : node.statements.body
    else
      []
    end
  end

  def collect_declaration(node, owner)
    name = declaration_name(node.constant_path, owner)
    module_declaration = node.is_a?(Prism::ModuleNode)
    identity = identity(module_declaration ? "type" : "class", name, ordinal(node))
    fact = {
      "declaration_id" => identity,
      "kind" => module_declaration ? "module" : "class",
      "name" => name,
      "visibility" => "public",
      "visibility_intent" => "public",
      "declaration_annotations" => [],
      "line_count" => line_count(node),
      "methods" => [],
      "abstract_methods" => [],
      "properties" => [],
      "signatures" => []
    }
    @declarations << fact
    if module_declaration && @namespaces.none? { |namespace| namespace.fetch("qualified_name") == name }
      @namespaces << {"kind" => "module", "qualified_name" => name}
    end
    if node.is_a?(Prism::ClassNode) && node.superclass
      @relations << relation(identity, "extends", node.superclass.slice)
    end
    collect_body(node.body, name, fact, false)
  end

  def collect_method(node, owner, declaration, visibility, singleton)
    singleton_method = singleton || !node.receiver.nil?
    method_visibility = if singleton
                          visibility
                        elsif node.receiver
                          "public"
                        else
                          visibility
                        end
    name = node.name.to_s
    kind = if !singleton_method && name == "initialize"
             "constructor"
           elsif singleton_method
             "type_method"
           else
             "instance_method"
           end
    qualified_name = "#{owner}.#{name}"
    parameters = parameters(node.parameters)
    optional_args = parameters.count { |parameter| parameter.fetch("has_default") }
    callable = {
      "declaration_id" => identity("method", qualified_name, ordinal(node)),
      "source_id" => @source_id,
      "name" => name,
      "qualified_name" => qualified_name,
      "owner_name" => owner,
      "kind" => kind,
      "visibility" => method_visibility,
      "visibility_intent" => method_visibility,
      "declaration_annotations" => [],
      "line_start" => node.location.start_line,
      "line_end" => node.location.end_line,
      "line_count" => line_count(node),
      "parameters" => parameters,
      "declared_args" => parameters.length,
      "optional_args" => optional_args,
      "return_annotation" => "",
      "decorators" => [],
      "docstring" => ""
    }
    summary = {
      "name" => name,
      "visibility" => callable.fetch("visibility"),
      "visibility_intent" => callable.fetch("visibility_intent"),
      "declaration_annotations" => [],
      "line_count" => callable.fetch("line_count"),
      "declared_args" => parameters.length,
      "optional_args" => optional_args
    }
    declaration.fetch("methods") << summary
    @callable_facts << {"node" => node, "json" => callable, "summary" => summary}
  end

  def parameters(node)
    return [] if node.nil?

    result = []
    node.requireds.each { |parameter| result << parameter_fact(parameter, "positional", false) }
    node.optionals.each { |parameter| result << parameter_fact(parameter, "positional", true) }
    result << parameter_fact(node.rest, "variadic_positional", false) if node.rest
    node.posts.each { |parameter| result << parameter_fact(parameter, parameter_kind(parameter), false) }
    node.keywords.each do |parameter|
      result << parameter_fact(parameter, "named_only", parameter.is_a?(Prism::OptionalKeywordParameterNode))
    end
    result << parameter_fact(node.keyword_rest, parameter_kind(node.keyword_rest), false) if node.keyword_rest
    result << parameter_fact(node.block, "named_only", false) if node.block
    result
  end

  def parameter_fact(node, kind, has_default)
    {
      "name" => parameter_name(node),
      "annotation" => "",
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
      next unless callable.fetch("owner_name") == owner && names.include?(callable.fetch("name"))
      instance_callable = callable.fetch("kind") == "instance_method" || callable.fetch("kind") == "constructor"
      type_callable = callable.fetch("kind") == "type_method"
      next unless singleton ? type_callable : instance_callable

      callable["visibility"] = visibility
      callable["visibility_intent"] = visibility
      fact.fetch("summary")["visibility"] = visibility
      fact.fetch("summary")["visibility_intent"] = visibility
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

  def collect_constant(node, owner)
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
    @values << {
      "declaration_id" => identity("value", name, ordinal(node)),
      "name" => name,
      "visibility" => "public",
      "visibility_intent" => "public",
      "line_count" => line_count(node),
      "declaration_kind" => "constant",
      "value_kind" => value_kind,
      "scope" => "module",
      "declared_args" => 0,
      "optional_args" => 0
    }
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
        target = call_target(node, callable.fetch("owner_name"))
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
    return "#{owner}.#{name}" if node.receiver.nil? || self_receiver?(node.receiver)

    receiver = constant_reference(node.receiver)
    return nil if receiver.nil?

    normalized = receiver.sub(/\A::/, "").gsub("::", ".")
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
      next if stop_at_definitions && child.is_a?(Prism::DefNode)

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
    {"source_id" => @source_id, "family" => family, "qualified_name" => name, "ordinal" => ordinal}
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
    values = @values.count { |value| value.fetch("visibility") == "public" }
    declarations + values
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
