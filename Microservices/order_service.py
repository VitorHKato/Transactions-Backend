from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

INVENTORY_SERVICE_URL = 'http://127.0.0.1:5001'
PAYMENT_SERVICE_URL = 'http://127.0.0.1:5002'
SHIPPING_SERVICE_URL = 'http://127.0.0.1:5003'


@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    product_id = data['product_id']
    quantity = data['quantity']

    try:
        # Check inventory
        inventory_response = requests.post(f'{INVENTORY_SERVICE_URL}/reserve', json={'product_id': product_id,
                                                                                     'quantity': quantity})
        # inventory_response.raise_for_status()
        if inventory_response.status_code in (400, 500):
            return jsonify(inventory_response.json()), inventory_response.status_code

        # Process payment
        payment_response = requests.post(f'{PAYMENT_SERVICE_URL}/pay',
                                         json={'amount': inventory_response.json()['total_price']})
        # payment_response.raise_for_status()
        if payment_response.status_code in (400, 500):
            return jsonify(payment_response.json()), payment_response.status_code

        # Ship order
        shipping_response = requests.post(f'{SHIPPING_SERVICE_URL}/ship', json={'product_id': product_id,
                                                                                'quantity': quantity})
        # shipping_response.raise_for_status()
        if shipping_response.status_code in (400, 500):
            return jsonify(shipping_response.json()), shipping_response.status_code

        return jsonify({"message": "Order processed successfully!"}), 200
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)

