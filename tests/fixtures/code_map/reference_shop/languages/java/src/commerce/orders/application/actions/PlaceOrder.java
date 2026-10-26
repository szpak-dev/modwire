package commerce.orders.application.actions;

import commerce.orders.domain.model.Order;
import commerce.orders.domain.services.OrderPolicy;

public final class PlaceOrder {
    private final OrderPolicy policy;

    public PlaceOrder(OrderPolicy policy) {
        this.policy = policy;
    }

    public boolean place(Order order) {
        if (!policy.allows(order)) {
            return false;
        }
        order.markPlaced();
        return true;
    }
}
