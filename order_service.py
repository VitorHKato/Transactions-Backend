from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

INVENTORY_SERVICE_URL = 'http://localhost:5001'
PAYMENT_SERVICE_URL = 'http://localhost:5002'
SHIPPING_SERVICE_URL = 'http://localhost:5003'


@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    product_id = data['product_id']
    quantity = data['quantity']

    try:
        # Check inventory
        inventory_response = requests.post(f'{INVENTORY_SERVICE_URL}/reserve', json={'product_id': product_id,
                                                                                     'quantity': quantity})
        inventory_response.raise_for_status()

        # Process payment
        payment_response = requests.post(f'{PAYMENT_SERVICE_URL}/pay',
                                         json={'amount': inventory_response.json()['total_price']})
        payment_response.raise_for_status()

        # Ship order
        shipping_response = requests.post(f'{SHIPPING_SERVICE_URL}/ship', json={'product_id': product_id,
                                                                                'quantity': quantity})
        shipping_response.raise_for_status()

        return jsonify({"message": "Order processed successfully!"}), 200
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=500, debug=True)

