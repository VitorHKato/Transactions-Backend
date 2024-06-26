from flask import Flask, request, jsonify
from sqlalchemy import Column, Integer, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


app = Flask(__name__)


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


@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    product_id = data['product_id']
    quantity = data['quantity']
    user_id = data['user_id']

    session = Session()
    try:
        new_order = Orders(
            user_id=user_id,
            product_id=product_id,
            itens_qtt=quantity
        )
        session.add(new_order)
        session.flush()

        # Created restore point
        checkpoint_id = session.execute(text("SELECT last_insert_rowid()")).scalar()

        return jsonify({"checkpoint_id": checkpoint_id}), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@app.route('/order_rollback', methods=['POST'])
def order_rollback():
    session = Session()
    try:
        data = request.json
        checkpoint_id = data['checkpoint_id']

        # Revert restore point
        session.execute(text(f"ROLLBACK TO SAVEPOINT checkpoint_{checkpoint_id}"))
        session.commit()

        return jsonify({"error": "Order process rolled back."}), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@app.route('/order_commit/<int:checkpoint_id>', methods=['POST'])
def order_commit(checkpoint_id):
    session = Session()
    try:
        order = session.query(Orders).get(checkpoint_id)
        order.status = 'committed'
        session.commit()
        return jsonify({"message": "Order committed"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


if __name__ == '__main__':
    app.run(port=5000, debug=True)
