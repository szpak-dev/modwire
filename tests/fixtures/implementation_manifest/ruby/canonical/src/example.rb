require "json"

module ExampleFormatting
  def example_format(example_value)
    example_value.upcase
  end
end

module ExampleValidation
end

module ExampleClassMethods
end

class ExampleAbstract
  include ExampleFormatting
  prepend ExampleValidation
  extend ExampleClassMethods

  EXAMPLE_CONSTANT = "example"
  EXAMPLE_CALLBACK = ->(example_value) { example_value }

  def initialize(example_name)
    @example_name = example_name
  end

  def example_required(example_value, example_optional = "optional", *example_items, example_named:, example_default: "default", **example_options, &example_block)
    example_format(example_value)
    JSON.generate(items: example_items, named: example_named, default: example_default, options: example_options)
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
  end
end
