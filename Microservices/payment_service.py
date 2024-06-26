import requests
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Float, Integer, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from orchestrator import PRODUCT_SERVICE_URL

app = Flask(__name__)


DATABASE_URI = 'sqlite:///payment.db'
Base = declarative_base()
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)


class Payment(Base):
    __tablename__ = 'payment'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)


Base.metadata.create_all(engine)


@app.route('/pay', methods=['POST'])
def process_payment():
    data = request.json
    user_id = data['user_id']
    amount = data['total_price']

    session = Session()
    try:
        response_user = requests.put(f'{PRODUCT_SERVICE_URL}/user/{user_id}', json={'total_price': amount})

        if response_user.status_code != 200:
            return jsonify({"error": response_user.json()['error']}), response_user.status_code

        if response_user.json()['balance'] < 0:
            return jsonify({"error": "User has no enough balance."}), 500

        new_payment = Payment(
            user_id=user_id,
            amount=amount
        )

        session.add(new_payment)
        session.commit()

        # Created restore point
        checkpoint_id = session.execute(text("SELECT last_insert_rowid()")).scalar()

        return jsonify({"checkpoint_id": checkpoint_id}), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@app.route('/pay_rollback', methods=['POST'])
def payment_rollback():
    session = Session()
    try:
        data = request.json
        checkpoint_id = data['checkpoint_id']

        # Revert restore point
        session.execute(text(f"ROLLBACK TO SAVEPOINT checkpoint_{checkpoint_id}"))
        session.commit()

        return jsonify({"error": "Payment process rolled back."}), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@app.route('/payment_commit/<int:checkpoint_id>', methods=['POST'])
def payment_commit(checkpoint_id):
    session = Session()
    try:
        payment = session.query(Payment).get(id=checkpoint_id)
        session.commit()
        return jsonify({"message": "Payment committed"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


if __name__ == '__main__':
    app.run(port=5002, debug=True)

