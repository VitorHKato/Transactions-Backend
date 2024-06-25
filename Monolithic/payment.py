from models import Payment

def process_payment(user_id, total_price):
    # Payment stuff

    new_payment = Payment(
        user_id=user_id,
        amount=total_price
    )

    return new_payment
