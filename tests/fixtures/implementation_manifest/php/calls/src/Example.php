<?php
function exampleTarget(string $exampleValue): string
{
    return $exampleValue;
}

function exampleSource(string $exampleValue): string
{
    exampleTarget($exampleValue);
    return exampleTarget($exampleValue);
}
