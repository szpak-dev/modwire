require_relative "../../domain/model/payment"

class CapturePayment
  def capture(payment)
    payment.capture
  end
end
