from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from models import Product, Orders, Inventory, Payment
from db_conf import Session

product_bp = Blueprint('product_bp', __name__)


@product_bp.route('/product', methods=['POST'])
def add_product():
    session = Session()
    try:
        data = request.json
        new_product = Product(
            name=data['name'],
            price=data['price']
        )
        session.add(new_product)
        session.flush()

        if new_product.id:
            new_inventory = Inventory(
                product_id=new_product.id,
                stock=data['stock']
            )
            session.add(new_inventory)

        session.commit()
        return jsonify({"message": "Product added successfully!"}), 201
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@product_bp.route('/products', methods=['GET'])
def get_products():
    session = Session()
    try:
        all_products = session.query(Product).all()
        products_list = [{"id": product.id, "name": product.name, "price": product.price} for product in all_products]
        return jsonify(products_list), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@product_bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=id).first()
        inventory = session.query(Inventory).filter_by(product_id=id).first()
        if product:
            product_data = {"id": product.id, "name": product.name, "price": product.price}
            if inventory:
                product_data["stock"] = inventory.stock
            else:
                product_data["stock"] = None

            return jsonify(product_data), 200
        else:
            return jsonify({"error": "Product not found."}), 404
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@product_bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    session = Session()
    try:
        data = request.json
        product = session.query(Product).filter_by(id=id).first()
        inventory = session.query(Inventory).filter_by(product_id=id).first()
        if product:
            product.name = data['name'] if 'name' in data else product.name
            product.price = data['price'] if 'price' in data else product.price
            if inventory:
                inventory.stock = data['stock'] if 'stock' in data else inventory.stock

            session.commit()
            return jsonify({"message": "Product updated successfully!"}), 200
        else:
            return jsonify({"error": "Product not found."}), 404
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@product_bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=id).first()
        if product:
            session.delete(product)
            session.commit()
            return jsonify({"message": "Product deleted successfully!"}), 200
        else:
            return jsonify({"error": "Product not found."}), 404
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@product_bp.route('/list_all', methods=['GET'])
def list_all():
    session = Session()
    try:
        products = session.query(Product).all()
        products_list = [{"id": product.id, "name": product.name, "price": product.price}
                         for product in products]

        orders = session.query(Orders).all()
        orders_list = [{"id": order.id, "user_id": order.user_id, "product_id": order.product_id,
                        "itens_qtt": order.itens_qtt} for order in orders]

        inventory = session.query(Inventory).all()
        inventory_list = [{"id": i.id, "product_id": i.product_id, "stock": i.stock}
                          for i in inventory]

        payments = session.query(Payment).all()
        payment_list = [{"id": payment.id, "user_id": payment.user_id, "amount": payment.amount}
                        for payment in payments]

        return jsonify({"products": products_list, "orders": orders_list, "inventory": inventory_list,
                        "payments": payment_list}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

