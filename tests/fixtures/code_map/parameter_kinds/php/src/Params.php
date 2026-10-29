<?php

function exampleParameters(string $exampleValue, string ...$exampleRest): string
{
    return $exampleValue . implode('', $exampleRest);
}
