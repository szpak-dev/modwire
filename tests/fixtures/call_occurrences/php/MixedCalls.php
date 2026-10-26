<?php

final class ExampleValue {}

function example_inner(): int
{
    return 1;
}

function example_outer(int $exampleValue): int
{
    return $exampleValue;
}

function example_mixed_caller(): void
{
    example_outer(example_inner());
    new ExampleValue();
}
