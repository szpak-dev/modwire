<?php
namespace ModwireFixture\Commerce\Orders\Domain\Model;

final class Order
{
    private bool $placed = false;

    public function __construct(public readonly string $orderId) {}

    public function markPlaced(): void
    {
        $this->placed = true;
    }

    public function isPlaced(): bool
    {
        return $this->placed;
    }
}
