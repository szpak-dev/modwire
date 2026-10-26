package commerce.orders.domain.model;

public final class Order {
    public final String orderId;
    private boolean placed;

    public Order(String orderId) {
        this.orderId = orderId;
        this.placed = false;
    }

    public void markPlaced() {
        this.placed = true;
    }

    public boolean isPlaced() {
        return placed;
    }
}
