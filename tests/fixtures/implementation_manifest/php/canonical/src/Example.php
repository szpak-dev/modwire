<?php
namespace ExampleManifest;

use DateTimeImmutable;

interface ExampleContract
{
    public function exampleRequired(string $exampleValue): string;
}

trait ExampleFormatting
{
    public function exampleFormat(string $exampleValue): string
    {
        return strtoupper($exampleValue);
    }
}

abstract class ExampleAbstract
{
    abstract public function exampleRequired(string $exampleValue): string;
}

#[\Attribute]
final class ExampleImplementation extends ExampleAbstract implements ExampleContract
{
    use ExampleFormatting;

    public static string $exampleStatic = 'static';

    public function __construct(public ?string $exampleOptional = null) {}

    public function exampleRequired(string $exampleValue): string
    {
        return $exampleValue;
    }

    public function exampleTimestamp(string $exampleValue): string
    {
        return (new DateTimeImmutable())->format('c') . $this->exampleFormat($exampleValue);
    }
}

function exampleFunction(string $exampleValue, string $exampleSuffix = 'suffix'): string
{
    return $exampleValue . $exampleSuffix;
}
