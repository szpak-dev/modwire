import { Payment } from '../../domain/model/payment';

export class CapturePayment {
    capture(payment: Payment): void {
        payment.capture();
    }
}
