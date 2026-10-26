export class Payment {
    private captured = false;

    constructor(public readonly paymentId: string) {}

    capture(): void {
        this.captured = true;
    }
}
