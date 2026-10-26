class ExampleValue
end

def example_inner
  1
end

def example_outer(example_value)
  example_value
end

def example_mixed_caller
  example_outer(example_inner)
  ExampleValue.new
end
