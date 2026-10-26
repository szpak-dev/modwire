<?php

function example_target(): int
{
    return 1;
}

function example_caller(): void
{
    example_target();
    example_target();
}
