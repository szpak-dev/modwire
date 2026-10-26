require "json"
require_relative "../../domain/model/order"

class OrderRepository
  def initialize(root)
    @root = root
  end

  def save(order)
    JSON.generate(root: @root, order_id: order.order_id)
  end
end
