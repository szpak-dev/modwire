package commerce.orders.domain.services;

import commerce.orders.domain.model.Order;

public final class OrderPolicy {
    public boolean allows(Order order) {
        return !order.isPlaced();
    }
}
