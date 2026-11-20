class ExampleReceiver
  def example_instance
    def self.example_nested_instance
    end
    class << self
      def example_nested_singleton
      end
    end
    def ExampleReceiver.example_explicit_type
    end
  end

  def self.example_type
    def self.example_nested_type
    end
    class << self
      def example_nested_type_singleton
      end
    end
  end
end
