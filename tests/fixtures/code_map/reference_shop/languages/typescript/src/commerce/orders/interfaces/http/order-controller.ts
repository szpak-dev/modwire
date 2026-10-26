import { PlaceOrder } from '../../application/actions/place-order';
import { Order } from '../../domain/model/order';

export class OrderController {
    constructor(private readonly action: PlaceOrder) {}

    handle(orderId: string): boolean {
        return this.action.place(new Order(orderId));
    }
}
