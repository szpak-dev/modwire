class ExampleValue
  attr_reader :example_runtime_member

  def initialize
    @example_runtime_member = "runtime"
  end

  define_method(:example_generated_method) do |example_value|
    example_value
  end
end
