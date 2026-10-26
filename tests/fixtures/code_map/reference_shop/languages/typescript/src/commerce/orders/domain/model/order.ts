export class Order {
    private placed = false;

    constructor(public readonly orderId: string) {}

    markPlaced(): void {
        this.placed = true;
    }

    isPlaced(): boolean {
        return this.placed;
    }
}
