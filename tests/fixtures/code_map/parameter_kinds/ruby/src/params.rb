def example_parameters(example_value, *example_rest, example_named:, **example_options, &example_block)
  example_block&.call(example_value, example_rest, example_named, example_options)
end
