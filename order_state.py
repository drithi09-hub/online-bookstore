
from abc import ABC, abstractmethod


# State Interface
class OrderState(ABC):

    @abstractmethod
    def next_state(self, order):
        pass

    @abstractmethod
    def get_status(self):
        pass


# Placed State
class PlacedState(OrderState):

    def next_state(self, order):
        order.state = ConfirmedState()

    def get_status(self):
        return "PLACED"


# Confirmed State
class ConfirmedState(OrderState):

    def next_state(self, order):
        order.state = ShippedState()

    def get_status(self):
        return "CONFIRMED"


# Shipped State
class ShippedState(OrderState):

    def next_state(self, order):
        order.state = DeliveredState()

    def get_status(self):
        return "SHIPPED"


# Delivered State
class DeliveredState(OrderState):

    def next_state(self, order):
        raise ValueError("Order is already delivered")

    def get_status(self):
        return "DELIVERED"


# Order Context
class Order:

    def __init__(self, initial_status="PLACED"):

        states = {
            "PLACED": PlacedState(),
            "CONFIRMED": ConfirmedState(),
            "SHIPPED": ShippedState(),
            "DELIVERED": DeliveredState()
        }

        if initial_status not in states:
            raise ValueError("Invalid order status")

        self.state = states[initial_status]

    def move_to_next_state(self):
        self.state.next_state(self)

    def get_status(self):
        return self.state.get_status()
