<?php
namespace ExampleApp\ExampleDomain\ExampleModel;

use Stringable;

final class ExampleRecord implements Stringable
{
    public ?string $example_name = null;

    public function __construct(public string $example_id, public bool $example_active = false) {}

    public function __toString(): string
    {
        return $this->example_id;
    }
}
