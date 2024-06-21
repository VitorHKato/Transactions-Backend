from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/pay', methods=['POST'])
def process_payment():
    data = request.json
    amount = data['amount']

    if amount > 0:
        return jsonify({"message": "Payment processed"}), 200
    else:
        return jsonify({"error": "Invalid amount"}), 400


if __name__ == '__main__':
    app.run(port=5002, debug=True)

