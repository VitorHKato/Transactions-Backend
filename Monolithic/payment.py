from db_conf import Session
from models import Payment, User


def process_user_balance(user_id, total_price):
    session = Session()
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        user.balance -= total_price

        session.close()

        return user

    session.close()

    return None


def process_payment(user_id, total_price):
    new_payment = Payment(
        user_id=user_id,
        amount=total_price
    )

    return new_payment
