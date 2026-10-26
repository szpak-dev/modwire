class Order
  attr_reader :order_id

  def initialize(order_id)
    @order_id = order_id
    @placed = false
  end

  def mark_placed
    @placed = true
  end

  def is_placed
    @placed
  end
end
