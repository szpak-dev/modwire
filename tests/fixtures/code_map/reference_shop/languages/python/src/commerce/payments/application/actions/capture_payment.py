from commerce.payments.domain.model.payment import Payment


class CapturePayment:
    def capture(self, payment: Payment) -> None:
        payment.capture()
