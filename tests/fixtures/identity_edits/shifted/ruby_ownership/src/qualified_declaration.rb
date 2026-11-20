
module ExampleOuter
  module ExampleNested
  end

  class ExampleNested::ExampleTarget
  end

  def (ExampleNested::ExampleTarget).example_method
  end
end
