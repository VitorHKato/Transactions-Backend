
# Run
- python app.py (Monolithic)


## CRUD
- http://127.0.0.1:5000/product (POST)
	- {
		"name":  "Produto 3",
		"price":  200.50,
		"stock":  200
	}

- http://127.0.0.1:5000/products (GET)
- http://127.0.0.1:5000/products/3 (GET)
- http://127.0.0.1:5000/products/3 (PUT)
	- {
		"name":  "Produto 3",
		"price":  200.50,
		"stock":  200
	}
- http://127.0.0.1:5000/products/3 (DELETE)

### User
- http://127.0.0.1:5000/user (POST)
	- {
	    "balance": 200.00
	}


## List all from database
- http://127.0.0.1:5000/list_all (GET)


## Order
- http://127.0.0.1:5000/order (POST)
	- {
		"product_id": 2,
		"quantity": 100,
		"user_id": 2
	}
