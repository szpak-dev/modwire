<?php
namespace ExampleShapes;

use DateTimeImmutable;

const EXAMPLE_CONSTANT = 'example_constant';
$exampleVariable = 'example_variable';

interface ExampleContract
{
    public function exampleRequired(string $exampleValue): string;
}

abstract class ExampleAbstract
{
    abstract public function exampleRequired(string $exampleValue): string;

    public function exampleConcrete(): string
    {
        return 'example_value';
    }
}

#[\Attribute]
final class ExampleImplementation extends ExampleAbstract implements ExampleContract
{
    public function __construct(public ?string $exampleOptional = null) {}

    public function exampleRequired(string $exampleValue): string
    {
        return $exampleValue;
    }

    public function exampleTimestamp(string $exampleValue): string
    {
        return (new DateTimeImmutable())->format('c') . strlen($this->exampleRequired($exampleValue));
    }
}

function exampleFunction(string $exampleValue, string $exampleSuffix = 'example_suffix'): string
{
    return $exampleValue . $exampleSuffix;
}
