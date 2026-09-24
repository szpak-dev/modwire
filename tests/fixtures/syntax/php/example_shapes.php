<?php
namespace ExampleShapes;

const EXAMPLE_CONSTANT = 'example_constant';
$example_variable = 'example_variable';

interface ExampleContract
{
    public function example_required(string $example_value): string;
}

abstract class ExampleAbstract
{
    abstract public function example_required(string $example_value): string;

    public function example_concrete(): string
    {
        return 'example_value';
    }
}

class ExampleImplementation extends ExampleAbstract implements ExampleContract
{
    public ?string $example_optional = null;

    public function example_required(string $example_value): string
    {
        return $example_value;
    }
}

function example_function(string $example_value, string $example_suffix = 'example_suffix'): string
{
    return $example_value . $example_suffix;
}
