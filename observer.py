
from abc import ABC, abstractmethod


# Observer Interface
class OrderObserver(ABC):

    @abstractmethod
    def update(self, order_id, customer_email, message):
        pass


# Customer Notification Observer
class CustomerNotifier(OrderObserver):

    def update(self, order_id, customer_email, message):
        print("\n--- Customer Notification ---")
        print(f"Order ID: {order_id}")
        print(f"Customer Email: {customer_email}")
        print(f"Message: {message}")
        print("-----------------------------\n")


# Order Subject
class OrderSubject:

    def __init__(self):
        self.observers = []

    def attach(self, observer):
        self.observers.append(observer)

    def notify_observers(self, order_id, customer_email, message):
        for observer in self.observers:
            observer.update(order_id, customer_email, message)
