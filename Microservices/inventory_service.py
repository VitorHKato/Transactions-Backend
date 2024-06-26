import requests
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from order_service import PRODUCT_SERVICE_URL

app = Flask(__name__)

DATABASE_URI = 'sqlite:///inventory.db'
Base = declarative_base()
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)


class Inventory(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)


Base.metadata.create_all(engine)


@app.route('/reserve', methods=['POST'])
def reserve_inventory():
    session = Session()
    try:
        data = request.json
        product_id = data['product_id']
        quantity = data['quantity']

        inventory = session.query(Inventory).filter_by(product_id=product_id).first()
        product_response = requests.get(f'{PRODUCT_SERVICE_URL}/products/{product_id}')
        if not inventory:
            return jsonify({"error": "Product not available."}), 400
        elif inventory.stock < quantity:
            return jsonify({"error": "Insufficient stock."}), 400

        total_price = 0
        if product_response:
            total_price = product_response.json()['price'] * quantity

        inventory.stock -= quantity
        session.flush()

        # Created restore point
        checkpoint_id = session.execute(text("SELECT last_insert_rowid()")).scalar()

        return jsonify({"checkpoint_id": checkpoint_id, "total_price": total_price}), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@app.route('/reserve_rollback', methods=['POST'])
def rollback_inventory():
    session = Session()
    try:
        data = request.json
        checkpoint_id = data['checkpoint_id']

        # Revert restore point
        session.execute(text(f"ROLLBACK TO SAVEPOINT checkpoint_{checkpoint_id}"))
        session.commit()

        return jsonify({"error": "Inventory reservation rolled back."}), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@app.route('/add_inventory', methods=['POST'])
def add_inventory():
    session = Session()
    try:
        data = request.json
        product_id = data['product_id']
        quantity = data['stock']

        new_inventory = Inventory(
            product_id=product_id,
            stock=quantity
        )
        session.add(new_inventory)

        session.commit()
        return jsonify("Inventory added"), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@app.route('/get_inventory/<int:product_id>', methods=['GET'])
def get_inventory(product_id):
    session = Session()

    try:
        inventory = session.query(Inventory).filter_by(product_id=product_id).first()

        if inventory:
            return jsonify({"stock": inventory.stock}), 200
    except SQLAlchemyError as e:
        return jsonify({"error": "Inventory not found."}), 404
    finally:
        session.close()


if __name__ == '__main__':
    app.run(port=5001, debug=True)

