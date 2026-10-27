class ExampleCalls
  def example_target(example_value)
    example_value
  end

  def example_source(example_value)
    example_target(example_value)
    example_target(example_value)
  end
end
