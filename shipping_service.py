from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/ship', methods=['POST'])
def ship_order():
    data = request.json
    product_id = data['product_id']
    quantity = data['quantity']

    return jsonify({"message": "Order shipped"}), 200


if __name__ == '__main__':
    app.run(port=5003, debug=True)

