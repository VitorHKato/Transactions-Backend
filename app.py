from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from product import Product

app = Flask(__name__)

DATABASE_URI = 'sqlite:///ecommerce.db'
Base = declarative_base()
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)


Base.metadata.create_all(engine)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/product', methods=['POST'])
def add_product():
    session = Session()
    try:
        data = request.json
        new_product = Product(
            name=data['name'],
            price=data['price'],
            stock=data['stock']
        )

        session.add(new_product)
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
        products_list = [{"id": product.id, "name": product.name, "price": product.price, "stock": product.stock} for product in all_products]
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
            product_data = {"id": product.id, "name": product.name, "price": product.price, "stock": product.stock}
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
        if product:
            product.name = data['name'] if 'name' in data else product.name
            product.price = data['price'] if 'price' in data else product.price
            product.stock = data['stock'] if 'stock' in data else product.stock
            session.commit()
            return jsonify({"message": "Product updated successfully!"}), 200
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


@app.route('/order', methods=['POST'])
def process_order():
    session = Session()
    try:
        data = request.json
        product_id = data['product_id']
        quantity = data['quantity']

        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            return jsonify({"error": "Product not available."}), 400
        elif product.stock < quantity:
            return jsonify({"error": "Insufficient stock."})

        total_price = product.price * quantity

        #2-Phase commit
        try:
            product.stock -= quantity
            session.flush() # Ensure changes are flushed to the database for locking
            # Simulate payment processing
            # If payment fails, raise an exception to rollback
            # raise SQLAlchemyError("Payment processing failed")
        except SQLAlchemyError as e:
            session.rollback()
            raise e

        session.commit()
        return jsonify({"message": "Order processed successfully", "total_price": total_price}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


if __name__ == '__main__':
    app.run(debug=True)
