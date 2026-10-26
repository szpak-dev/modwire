package commerce.payments.domain.model;

public final class Payment {
    private final String paymentId;
    private boolean captured;

    public Payment(String paymentId) {
        this.paymentId = paymentId;
        this.captured = false;
    }

    public void capture() {
        this.captured = true;
    }
}
