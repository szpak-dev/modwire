require "json"

example_dependency = "yaml"
require example_dependency

module ExampleIncluded
  def example_included(example_value)
    example_value
  end
end

module ExamplePrepended
end

module ExampleExtended
end

ExampleDynamicNamespace = Module.new
ExampleGenerated = Class.new

class ExampleBase
  include ExampleIncluded
  prepend ExamplePrepended
  extend ExampleExtended

  EXAMPLE_LITERAL = "example"
  attr_reader :example_generated_attribute

  sig { params(example_value: String).returns(String) }
  def initialize(example_value, example_optional = "optional", *example_items, example_named:, example_default: "default", **example_options, &example_block)
    @example_generated_attribute = example_value
  end

  def example_local(example_value)
    example_value
  end

  def example_calls(example_receiver)
    example_local(example_receiver)
    example_missing(example_receiver)
    example_receiver.public_send(:example_dynamic)
  end

  def example_forwarding(...)
    example_calls(...)
  end

  def self.example_hidden(example_value)
    example_value
  end

  private_class_method :example_hidden

  define_method(:example_generated_method) do |example_generated_parameter|
    example_generated_call(example_generated_parameter)
    example_generated_parameter
  end
end

ExampleRuntimeBase = ExampleBase

class ExampleRuntime < ExampleRuntimeBase
end

ExampleRuntime.include(ExampleIncluded)
