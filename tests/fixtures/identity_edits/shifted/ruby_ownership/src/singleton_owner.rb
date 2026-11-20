
class ExampleTarget
end

class ExampleContainer
  class << ExampleTarget
    attr_reader :example_value
  end
end
