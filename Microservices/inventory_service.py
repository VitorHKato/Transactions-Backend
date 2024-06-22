from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from product import Product

app = Flask(__name__)

DATABASE_URI = 'sqlite:///inventory.db'
Base = declarative_base()
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)


Base.metadata.create_all(engine)


@app.route('/reserve', methods=['POST'])
def reserve_inventory():
    session = Session()
    try:
        data = request.json
        product_id = data['product_id']
        quantity = data['quantity']

        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            return jsonify({"error": "Product not available."}), 400
        elif product.stock < quantity:
            return jsonify({"error": "Insufficient stock."}), 400

        product.stock -= quantity
        session.commit()
        return jsonify({"total_price": product.price * quantity}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


if __name__ == '__main__':
    app.run(port=5001, debug=True)

