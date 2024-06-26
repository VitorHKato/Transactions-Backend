import requests
from flask import Flask, request, jsonify

app = Flask(__name__)


ORDER_SERVICE_URL = 'http://127.0.0.1:5000'
INVENTORY_SERVICE_URL = 'http://127.0.0.1:5001'
PAYMENT_SERVICE_URL = 'http://127.0.0.1:5002'
PRODUCT_SERVICE_URL = 'http://127.0.0.1:5003'


@app.route('/order', methods=['POST'])
def order():
    data = request.json
    product_id = data['product_id']
    quantity = data['quantity']
    user_id = data['user_id']

    checkpoint_ids = {}

    try:
        # Create order
        order_response = requests.post(f'{ORDER_SERVICE_URL}/create_order', json={'product_id': product_id,
                                                                             'quantity': quantity, 'user_id': user_id})

        if order_response.status_code in (400, 500):
            raise Exception("Order creation failed", 'order', order_response.json()['checkpoint_id'])

        checkpoint_ids['order'] = order_response.json().get('checkpoint_id')

        # Check inventory
        inventory_response = requests.post(f'{INVENTORY_SERVICE_URL}/reserve', json={'product_id': product_id,
                                                                                     'quantity': quantity})

        if inventory_response.status_code in (400, 500):
            raise Exception("Inventory creation failed", 'order', inventory_response.json()['checkpoint_id'])

        checkpoint_ids['inventory'] = inventory_response.json().get('checkpoint_id')

        # Process payment
        payment_response = requests.post(f'{PAYMENT_SERVICE_URL}/pay',
                                         json={'user_id': user_id,
                                               'total_price': inventory_response.json()['total_price']})

        if payment_response.status_code in (400, 500):
            raise Exception("Payment creation failed", 'order', payment_response.json()['checkpoint_id'])

        checkpoint_ids['payment'] = payment_response.json().get('checkpoint_id')

        # Commit all transactions
        requests.post(f'{ORDER_SERVICE_URL}/order_commit/{checkpoint_ids["order"]}')
        requests.post(f'{INVENTORY_SERVICE_URL}/reserve_commit/{checkpoint_ids["inventory"]}')
        requests.post(f'{PAYMENT_SERVICE_URL}/payment_commit/{checkpoint_ids["payment"]}')

        return jsonify({"message": "Order processed successfully", "total_price":
                inventory_response.json()['total_price']}), 200
    except Exception as e:
        error_message, failed_service, checkpoint_id = e.args

        rollback_errors = []

        if 'order' in checkpoint_ids:
            rollback_response = requests.post(f'{ORDER_SERVICE_URL}/order_rollback',
                                              json={'checkpoint_id': checkpoint_ids['order']})
            if rollback_response.status_code != 200:
                rollback_errors.append('Order rollback failed')
        if 'inventory' in checkpoint_ids:
            rollback_response = requests.post(f'{INVENTORY_SERVICE_URL}/reserve_rollback',
                                              json={'checkpoint_id': checkpoint_ids['inventory']})
            if rollback_response.status_code != 200:
                rollback_errors.append('Inventory rollback failed')
        if 'payment' in checkpoint_ids:
            rollback_response = requests.post(f'{PAYMENT_SERVICE_URL}/payment_rollback',
                                              json={'checkpoint_id': checkpoint_ids['payment']})
            if rollback_response.status_code != 200:
                rollback_errors.append('Payment rollback failed')

        return jsonify({"error": error_message, "rollback_errors": rollback_errors}), 400
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5004, debug=True)

