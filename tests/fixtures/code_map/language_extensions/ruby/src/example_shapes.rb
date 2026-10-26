require "json"
require_relative "example_support"

module ExampleLogging
  def example_log(example_value)
    example_value
  end
end

module ExampleValidation
end

module ExampleClassMethods
end

class ExampleAbstract
  include ExampleLogging
  prepend ExampleValidation
  extend ExampleClassMethods

  EXAMPLE_CONSTANT = "example_constant"
  EXAMPLE_CALLBACK = ->(example_value) { example_value }

  def initialize(example_name)
    @example_name = example_name
  end

  def example_required(example_value, example_optional = "example", *example_items, example_named:, example_default: "example", **example_options, &example_block)
    example_log(example_value)
    ExampleSupport.example_target(example_named)
    JSON.generate(example_items: example_items, example_default: example_default, example_options: example_options)
    example_block.call(@example_name) if example_block
  end

  def self.example_type_method(example_value)
    example_value
  end

  protected

  def example_protected
    @example_name
  end

  private

  def example_private
    example_protected
  end
end

class ExampleImplementation < ExampleAbstract
  def example_execute(example_value)
    example_required(example_value, example_named: example_value)
    example_missing(example_value)
  end
end
