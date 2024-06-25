from flask import Flask
from models import Base
from db_conf import engine
from product import product_bp
from order import order_bp

app = Flask(__name__)

# Create tables
Base.metadata.create_all(engine)


# Register Blueprints
app.register_blueprint(product_bp)
app.register_blueprint(order_bp)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
