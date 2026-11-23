
class ExampleOwner
  @example_shared = 0

  def self.example_direct
    @example_value = 1
    example_lambda = -> { @example_lambda = 2 }
  end

  class << self
    @example_metaclass = 0
    def example_singleton
      @example_singleton = 3
    end
  end

  def example_instance
    @example_value = 4
  end
end
