import requests
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from orchestrator import INVENTORY_SERVICE_URL
from inventory_service import Inventory
from order_service import Orders
from payment_service import Payment

app = Flask(__name__)


DATABASE_URI = 'sqlite:///product.db'
Base = declarative_base()
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    balance = Column(Float, nullable=False)


Base.metadata.create_all(engine)


@app.route('/product', methods=['POST'])
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
            inventory_response = requests.post(f'{INVENTORY_SERVICE_URL}/add_inventory', json={'product_id': new_product.id,
                                                                                         'stock': data['stock']})

            if inventory_response.status_code in (400, 500):
                return jsonify(inventory_response.json()), inventory_response.status_code

        session.commit()
        return jsonify({"message": "Product added successfully!"}), 201
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route('/products', methods=['GET'])
def get_products():
    session = Session()
    try:
        all_products = session.query(Product).all()
        products_list = [{"id": product.id, "name": product.name, "price": product.price} for product in all_products]

        for p in products_list:
            inventory_response = requests.get(f'{INVENTORY_SERVICE_URL}/get_inventory/{p["id"]}')
            if inventory_response.status_code == 200:
                inventory_data = inventory_response.json()
                p["stock"] = inventory_data.get('stock')
            else:
                p["stock"] = None

        return jsonify(products_list), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=id).first()
        if product:
            product_data = {"id": product.id, "name": product.name, "price": product.price}
            inventory_response = requests.get(f'{INVENTORY_SERVICE_URL}/get_inventory/{product.id}')
            if inventory_response.status_code == 200:
                inventory_data = inventory_response.json()
                product_data["stock"] = inventory_data.get('stock')
            else:
                product_data["stock"] = None

            return jsonify(product_data), 200
        else:
            return jsonify({"error": "Product not found."}), 404
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    session = Session()
    try:
        data = request.json
        product = session.query(Product).filter_by(id=id).first()
        inventory = requests.get(f'{INVENTORY_SERVICE_URL}/get_inventory/{product.id}')
        if product:
            product.name = data['name'] if 'name' in data else product.name
            product.price = data['price'] if 'price' in data else product.price
            if inventory:
                inventory_response = requests.put(f'{INVENTORY_SERVICE_URL}/inventory/{inventory.json()["id"]}', json={'stock': data['stock']})

                if inventory_response.status_code == 200:
                    session.commit()
                    return jsonify({"message": "Product updated successfully!"}), 200
            return jsonify({"error": "Error updating stock"}), 400
        else:
            return jsonify({"error": "Product not found."}), 404
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route('/products/<int:id>', methods=['DELETE'])
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


@app.route('/list_all', methods=['GET'])
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


@app.route('/user', methods=['POST'])
def add_user():
    session = Session()
    try:
        data = request.json
        new_user = User(
            balance=data['balance']
        )
        session.add(new_user)

        session.commit()
        return jsonify({"message": "User added successfully!"}), 201
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route('/user/<int:id>', methods=['GET'])
def get_user(id):
    session = Session()
    try:
        user = session.query(User).filter_by(id=id).first()
        if user:
            user_data = {"id": user.id, "balance": user.balance}

            return jsonify(user_data), 200
        else:
            return jsonify({"error": "User not found."}), 404
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route('/user/<int:id>', methods=['PUT'])
def update_user(id):
    session = Session()
    try:
        data = request.json
        user = session.query(User).filter_by(id=id).first()
        if user:
            user.balance -= data['total_price']
            session.commit()

            return jsonify({"message": "New user balance: {}".format(user.balance)}), 200
        else:
            return jsonify({"error": "User not found."}), 404
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


if __name__ == '__main__':
    app.run(port=5003, debug=True)

