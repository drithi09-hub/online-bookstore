
from abc import ABC, abstractmethod


# Strategy Interface
class PaymentStrategy(ABC):

    @abstractmethod
    def pay(self, amount):
        pass


# Credit/Debit Card Payment
class CardPayment(PaymentStrategy):

    def pay(self, amount):
        return {
            "success": True,
            "method": "Card",
            "message": f"Card payment of ${amount:.2f} simulated successfully."
        }


# PayPal Payment
class PayPalPayment(PaymentStrategy):

    def pay(self, amount):
        return {
            "success": True,
            "method": "PayPal",
            "message": f"PayPal payment of ${amount:.2f} simulated successfully."
        }


# Cash on Delivery
class CashOnDelivery(PaymentStrategy):

    def pay(self, amount):
        return {
            "success": True,
            "method": "Cash on Delivery",
            "message": "Order placed. Payment will be collected on delivery."
        }


# Payment Context
class PaymentContext:

    def __init__(self, strategy: PaymentStrategy):
        self.strategy = strategy

    def process_payment(self, amount):
        return self.strategy.pay(amount)
