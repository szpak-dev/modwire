package commerce.payments.application.actions;

import commerce.payments.domain.model.Payment;

public final class CapturePayment {
    public void capture(Payment payment) {
        payment.capture();
    }
}
