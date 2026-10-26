<?php
namespace ModwireFixture\Commerce\Orders\Infrastructure\Repositories;

use DateTimeImmutable;
use ModwireFixture\Commerce\Orders\Domain\Model\Order;

final class OrderRepository
{
    public function __construct(private readonly string $root) {}

    public function save(Order $order): string
    {
        return $this->root . '/' . $order->orderId . (new DateTimeImmutable())->format('c');
    }
}
