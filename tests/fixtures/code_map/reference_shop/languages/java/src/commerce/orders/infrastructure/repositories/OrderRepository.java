package commerce.orders.infrastructure.repositories;

import commerce.orders.domain.model.Order;
import java.time.Instant;

public final class OrderRepository {
    private final String root;

    public OrderRepository(String root) {
        this.root = root;
    }

    public String save(Order order) {
        return root + "/" + order.orderId + Instant.now();
    }
}
