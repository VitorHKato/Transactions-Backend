from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from inventory import process_inventory
from payment import process_payment
from models import Product, Inventory, Orders
from db_conf import Session


order_bp = Blueprint('order_bp', __name__)


@order_bp.route('/order', methods=['POST'])
def process_order():
    session = Session()
    try:
        data = request.json
        product_id = data['product_id']
        quantity = data['quantity']
        user_id = data['user_id']

        product = session.query(Product).filter_by(id=product_id).first()
        inventory = session.query(Inventory).filter_by(id=product_id).first()
        if not product:
            return jsonify({"error": "Product not available."}), 400

        # 2-Phase commit (1 phase)
        new_order = Orders(
            user_id=user_id,
            product_id=product_id,
            itens_qtt=quantity
        )
        session.add(new_order)
        session.flush()

        total_price = product.price * quantity

        try:
            # Process inventory
            process_inventory(quantity, inventory)
            session.flush()         # Temporary persistence

            # Process payment
            new_payment = process_payment(user_id, total_price)
            session.add(new_payment)
            session.flush()

        except SQLAlchemyError as e:
            session.rollback()
            raise e

        # 2-Phase commit (2 phase)
        session.commit()
        return jsonify({"message": "Order processed successfully", "total_price": total_price}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

