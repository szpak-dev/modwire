<?php
namespace ModwireFixture\Commerce\Orders\Domain\Services;

use ModwireFixture\Commerce\Orders\Domain\Model\Order;

final class OrderPolicy
{
    public function allows(Order $order): bool
    {
        return !$order->isPlaced();
    }
}
