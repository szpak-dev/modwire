require "json"

class ExampleDependency
  def example_json(example_value)
    JSON.generate(example: example_value)
  end
end
