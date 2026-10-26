package commerce.orders.interfaces.http;

import commerce.orders.application.actions.PlaceOrder;
import commerce.orders.domain.model.Order;

public final class OrderController {
    private final PlaceOrder action;

    public OrderController(PlaceOrder action) {
        this.action = action;
    }

    public boolean handle(String orderId) {
        return action.place(new Order(orderId));
    }
}
