from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

DATABASE_URI = 'sqlite:///ecommerce.db'
Base = declarative_base()
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)


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
