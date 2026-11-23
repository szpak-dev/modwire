require "example/root"

module Example
  class Owner
    attr_reader :example_value
    attr_accessor :example_value

    def example_outer(example_value = require("example/default"))
      require_relative "example/local"
      example_call
      example_proc = ->(example_argument = require("example/lambda-default")) { example_lambda_call }
      example_items.each { example_block_call }
      def example_inner
        example_inner_call
      end
    end
  end
end
