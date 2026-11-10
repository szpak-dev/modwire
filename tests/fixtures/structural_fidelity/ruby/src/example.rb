module ExampleIncluded
end
module ExamplePrepended
end
module ExampleExtended
end

class ExampleBase
end

class ExampleOwner < ExampleBase
  include ExampleIncluded
  prepend ExamplePrepended
  extend ExampleExtended
  attr_accessor :example_value

  class ExampleNested
    def example_method(example_value)
      example_value
    end
  end

  def initialize(example_value)
    @example_value = example_value
  end

  def example_method(example_value, example_default = "", *example_rest, example_named:, **example_options, &example_block)
    example_value
  end
  alias example_alias example_method

  def self.example_direct(example_value)
    example_value
  end

  class << self
    def example_singleton(example_value)
      example_value
    end
  end

  def example_forward(...)
    example_method(...)
  end
end

class ExampleOther
  def example_method(example_value)
    example_value
  end
end

class ExampleOwner
  def example_reopened(example_value)
    example_value
  end
end
