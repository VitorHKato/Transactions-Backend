from sqlalchemy.exc import SQLAlchemyError


def process_inventory(quantity, inventory):
    if inventory.stock < quantity:
        raise SQLAlchemyError("Insufficient stock.")
    inventory.stock -= quantity

