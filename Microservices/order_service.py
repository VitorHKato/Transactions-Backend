from flask import Flask, request, jsonify
import requests
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


app = Flask(__name__)


INVENTORY_SERVICE_URL = 'http://127.0.0.1:5001'
PAYMENT_SERVICE_URL = 'http://127.0.0.1:5002'
PRODUCT_SERVICE_URL = 'http://127.0.0.1:5003'


DATABASE_URI = 'sqlite:///order.db'
Base = declarative_base()
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)


class Orders(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    itens_qtt = Column(Integer, nullable=False)


Base.metadata.create_all(engine)


def add_order(product_id, quantity, user_id, order_session):
    new_order = Orders(
        user_id=user_id,
        product_id=product_id,
        itens_qtt=quantity
    )
    order_session.add(new_order)
    order_session.flush()


@app.route('/order', methods=['POST'])
def create_order():
    data = request.json
    product_id = data['product_id']
    quantity = data['quantity']
    user_id = data['user_id']

    order_session = Session()
    try:
        # Add order
        add_order(product_id, quantity, user_id, order_session)

        # Check inventory
        inventory_response = requests.post(f'{INVENTORY_SERVICE_URL}/reserve', json={'product_id': product_id,
                                                                                     'quantity': quantity})

        # Process payment
        payment_response = requests.post(f'{PAYMENT_SERVICE_URL}/pay',
                                         json={'user_id': user_id,
                                               'total_price': inventory_response.json()['total_price']})

        if inventory_response.status_code in (400, 500) or payment_response.status_code in (400, 500):
            order_session.rollback()

            checkpoint_id = inventory_response.json()['checkpoint_id']
            rollback_response = requests.post(f'{INVENTORY_SERVICE_URL}/reserve_rollback',
                                              json={'checkpoint_id': checkpoint_id})

            checkpoint_id2 = payment_response.json()['checkpoint_id']
            rollback_response2 = requests.post(f'{INVENTORY_SERVICE_URL}/payment_rollback',
                                              json={'checkpoint_id': checkpoint_id2})

            return jsonify({"error": "Error during the process. Transaction rolled back."}), 400

        order_session.commit()
        return jsonify({"message": "Order processed successfully!"}), 200
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)
