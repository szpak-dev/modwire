<?php
namespace ExampleCapabilityGaps;

#[\Attribute]
final class ExampleTypeMarker {}

#[\Attribute]
final class ExampleMethodMarker {}

trait ExampleTrait
{
    #[ExampleMethodMarker]
    public function exampleTraitValue(): string
    {
        return 'example_trait';
    }
}

#[ExampleTypeMarker]
final class ExampleConsumer
{
    use ExampleTrait;

    public string $exampleValue = 'example_value';
}

$exampleConsumer = new ExampleConsumer();
$exampleConsumer->exampleRuntimeMember = 'example_runtime_member';
