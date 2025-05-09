

from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()

    # Create Customers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Customers (
            CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            Email TEXT NOT NULL UNIQUE,
            Phone TEXT,
            Status TEXT CHECK(Status IN ('Regular', 'Silver', 'Gold', 'Platinum')) DEFAULT 'Regular'
        )
    ''')

    # Create CreditCards Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS CreditCards (
            CardNumber TEXT PRIMARY KEY,
            CustomerID INTEGER,
            CardType TEXT,
            SecurityCode TEXT,
            BillingAddress TEXT,
            ExpiryDate TEXT,
            FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ShippingAddresses (
            ShippingID INTEGER PRIMARY KEY AUTOINCREMENT,
            CustomerID INTEGER,
            AddressName TEXT,
            Street TEXT,
            City TEXT,
            State TEXT,
            ZipCode TEXT,
            Country TEXT,
            FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE CASCADE
    )
''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Products (
            ProductID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Description TEXT,
            RecommendedPrice REAL,
            ProductType TEXT,
            QuantityInStock INTEGER
    )
''')
    
    # Create Offers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Offers (
            OfferID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductID INTEGER,
            OfferPrice REAL,
            FOREIGN KEY (ProductID) REFERENCES Products(ProductID) ON DELETE CASCADE
    )
''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ShoppingBaskets (
        BasketID INTEGER PRIMARY KEY AUTOINCREMENT,
        CustomerID INTEGER UNIQUE,
        FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE CASCADE
    )
''')

# Basket Items Table (Many-to-Many: Baskets ↔ Products)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS BasketItems (
            BasketID INTEGER,
            ProductID INTEGER,
            Quantity INTEGER,
            PRIMARY KEY (BasketID, ProductID),
            FOREIGN KEY (BasketID) REFERENCES ShoppingBaskets(BasketID) ON DELETE CASCADE,
            FOREIGN KEY (ProductID) REFERENCES Products(ProductID) ON DELETE CASCADE
    )
''')
    
        # Transactions
    cursor.execute('''CREATE TABLE IF NOT EXISTS Transactions (
        TransactionID INTEGER PRIMARY KEY AUTOINCREMENT,
        CustomerID INTEGER,
        BasketID INTEGER,
        ShippingID INTEGER,
        TotalAmount REAL,
        PaymentConfirmed BOOLEAN,
        FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
        FOREIGN KEY (BasketID) REFERENCES ShoppingBaskets(BasketID),
        FOREIGN KEY (ShippingID) REFERENCES ShippingAddresses(ShippingID))''')

    # Payments
    cursor.execute('''CREATE TABLE IF NOT EXISTS Payments (
        PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
        TransactionID INTEGER,
        CardNumber TEXT,
        FOREIGN KEY (TransactionID) REFERENCES Transactions(TransactionID),
        FOREIGN KEY (CardNumber) REFERENCES CreditCards(CardNumber))''')

    # Shipments
    cursor.execute('''CREATE TABLE IF NOT EXISTS Shipments (
        ShipmentID INTEGER PRIMARY KEY AUTOINCREMENT,
        TransactionID INTEGER,
        DeliveryStatus TEXT,
        FOREIGN KEY (TransactionID) REFERENCES Transactions(TransactionID))''')


    conn.commit()
    conn.close()

# --- Routes for Section 1: Customers ---
@app.route('/')
def index():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Customers")
    customers = cursor.fetchall()
    conn.close()
    return render_template('index.html', customers=customers)

@app.route('/register', methods=['POST'])
def register():
    data = (
        request.form['FirstName'],
        request.form['LastName'],
        request.form['Email'],
        request.form['Phone'],
        request.form['Status']
    )
    try:
        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Customers (FirstName, LastName, Email, Phone, Status)
            VALUES (?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    except sqlite3.IntegrityError:
        return "Email already exists!", 400

# --- Routes for Section 2: Credit Card Management ---
@app.route('/credit-cards')
def credit_cards():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM CreditCards")
    cards = cursor.fetchall()
    cursor.execute("SELECT CustomerID, FirstName || ' ' || LastName FROM Customers")
    customers = cursor.fetchall()
    conn.close()
    return render_template('credit_cards.html', cards=cards, customers=customers)

@app.route('/add-card', methods=['POST'])
def add_card():
    data = (
        request.form['CardNumber'],
        request.form['CustomerID'],
        request.form['CardType'],
        request.form['SecurityCode'],
        request.form['BillingAddress'],
        request.form['ExpiryDate']
    )
    try:
        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO CreditCards (CardNumber, CustomerID, CardType, SecurityCode, BillingAddress, ExpiryDate)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        conn.close()
        return redirect(url_for('credit_cards'))
    except sqlite3.IntegrityError:
        return "Card already exists or Customer not found!", 400
    
@app.route('/shipping')
def shipping():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ShippingAddresses")
    addresses = cursor.fetchall()
    cursor.execute("SELECT CustomerID, FirstName || ' ' || LastName FROM Customers")
    customers = cursor.fetchall()
    conn.close()
    return render_template('shipping.html', addresses=addresses, customers=customers)

@app.route('/add-shipping', methods=['POST'])
def add_shipping():
    data = (
        request.form['CustomerID'],
        request.form['AddressName'],
        request.form['Street'],
        request.form['City'],
        request.form['State'],
        request.form['ZipCode'],
        request.form['Country']
    )
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ShippingAddresses (CustomerID, AddressName, Street, City, State, ZipCode, Country)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()
    return redirect(url_for('shipping'))

@app.route('/products')
def products():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Products")
    products = cursor.fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/add-product', methods=['POST'])
def add_product():
    data = (
        request.form['Name'],
        request.form['Description'],
        float(request.form['RecommendedPrice']),
        request.form['ProductType'],
        int(request.form['QuantityInStock'])
    )
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Products (Name, Description, RecommendedPrice, ProductType, QuantityInStock)
        VALUES (?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()
    return redirect(url_for('products'))

@app.route('/offers')
def offers():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT Offers.OfferID, Products.Name, Offers.OfferPrice
        FROM Offers
        JOIN Products ON Offers.ProductID = Products.ProductID
    ''')
    offers = cursor.fetchall()
    cursor.execute("SELECT ProductID, Name FROM Products")
    products = cursor.fetchall()
    conn.close()
    return render_template('offers.html', offers=offers, products=products)

@app.route('/add-offer', methods=['POST'])
def add_offer():
    data = (
        request.form['ProductID'],
        request.form['OfferPrice']
    )
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Offers (ProductID, OfferPrice)
        VALUES (?, ?)
    ''', data)
    conn.commit()
    conn.close()
    return redirect(url_for('offers'))

@app.route('/baskets')
def baskets():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT CustomerID, FirstName || ' ' || LastName FROM Customers")
    customers = cursor.fetchall()
    cursor.execute('''
        SELECT sb.BasketID, c.FirstName || ' ' || c.LastName, p.Name, bi.Quantity
        FROM BasketItems bi
        JOIN ShoppingBaskets sb ON bi.BasketID = sb.BasketID
        JOIN Products p ON bi.ProductID = p.ProductID
        JOIN Customers c ON sb.CustomerID = c.CustomerID
        ORDER BY sb.BasketID
    ''')
    basket_items = cursor.fetchall()
    cursor.execute("SELECT ProductID, Name FROM Products")
    products = cursor.fetchall()
    conn.close()
    return render_template('baskets.html', customers=customers, basket_items=basket_items, products=products)

@app.route('/add-to-basket', methods=['POST'])
def add_to_basket():
    customer_id = request.form['CustomerID']
    product_id = request.form['ProductID']
    quantity = int(request.form['Quantity'])

    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()

    # Create basket if not exists
    cursor.execute("SELECT BasketID FROM ShoppingBaskets WHERE CustomerID = ?", (customer_id,))
    basket = cursor.fetchone()
    if basket is None:
        cursor.execute("INSERT INTO ShoppingBaskets (CustomerID) VALUES (?)", (customer_id,))
        basket_id = cursor.lastrowid
    else:
        basket_id = basket[0]

    # Insert or update quantity
    cursor.execute('''
        INSERT INTO BasketItems (BasketID, ProductID, Quantity)
        VALUES (?, ?, ?)
        ON CONFLICT(BasketID, ProductID) DO UPDATE SET Quantity = Quantity + excluded.Quantity
    ''', (basket_id, product_id, quantity))

    conn.commit()
    conn.close()
    return redirect(url_for('baskets'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        customer_id = request.form['CustomerID']
        shipping_id = request.form['ShippingID']
        card = request.form['CardNumber']
        cursor.execute("SELECT BasketID FROM ShoppingBaskets WHERE CustomerID=?", (customer_id,))
        basket_id = cursor.fetchone()
        if not basket_id:
            return "No basket found"

        basket_id = basket_id[0]
        cursor.execute('''SELECT bi.Quantity, p.ProductID, p.RecommendedPrice,
                          o.OfferPrice, c.Status FROM BasketItems bi
                          JOIN Products p ON p.ProductID = bi.ProductID
                          JOIN Customers c ON c.CustomerID = ?
                          LEFT JOIN Offers o ON o.ProductID = p.ProductID
                          WHERE bi.BasketID = ?''', (customer_id, basket_id))
        items = cursor.fetchall()

        total = 0
        for qty, pid, price, offer, status in items:
            if status in ("Gold", "Platinum") and offer:
                total += offer * qty
            else:
                total += price * qty

        cursor.execute('''INSERT INTO Transactions (CustomerID, BasketID, ShippingID, TotalAmount, PaymentConfirmed)
                          VALUES (?, ?, ?, ?, ?)''', (customer_id, basket_id, shipping_id, total, True))
        txn_id = cursor.lastrowid
        cursor.execute('''INSERT INTO Payments (TransactionID, CardNumber) VALUES (?, ?)''', (txn_id, card))
        cursor.execute('''INSERT INTO Shipments (TransactionID, DeliveryStatus) VALUES (?, ?)''', (txn_id, "Processing"))
        conn.commit()
        conn.close()
        return f"Transaction completed successfully! Total = ${total:.2f}"
    else:
        cursor.execute("SELECT CustomerID, FirstName || ' ' || LastName FROM Customers")
        customers = cursor.fetchall()
        cursor.execute("SELECT ShippingID, AddressName FROM ShippingAddresses")
        addresses = cursor.fetchall()
        cursor.execute("SELECT CardNumber FROM CreditCards")
        cards = cursor.fetchall()
        conn.close()
        return render_template('checkout.html', customers=customers, addresses=addresses, cards=cards)

@app.route('/statistics')
def statistics():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    stats = {}

    # 1. Total amount per card
    cursor.execute("SELECT CardNumber, SUM(TotalAmount) FROM Payments JOIN Transactions USING(TransactionID) GROUP BY CardNumber")
    stats['card_totals'] = cursor.fetchall()

    # 2. Top 10 customers
    cursor.execute("SELECT Customers.FirstName || ' ' || Customers.LastName, SUM(TotalAmount) FROM Transactions JOIN Customers USING(CustomerID) GROUP BY CustomerID ORDER BY SUM(TotalAmount) DESC LIMIT 10")
    stats['top_customers'] = cursor.fetchall()

    # 3. Most frequently sold products
    cursor.execute("SELECT p.Name, SUM(bi.Quantity) FROM BasketItems bi JOIN Products p ON bi.ProductID = p.ProductID GROUP BY bi.ProductID ORDER BY SUM(bi.Quantity) DESC LIMIT 5")
    stats['popular_products'] = cursor.fetchall()

    # 4. Products with most distinct customers
    cursor.execute("SELECT p.Name, COUNT(DISTINCT sb.CustomerID) FROM BasketItems bi JOIN ShoppingBaskets sb ON bi.BasketID = sb.BasketID JOIN Products p ON bi.ProductID = p.ProductID GROUP BY bi.ProductID ORDER BY COUNT(DISTINCT sb.CustomerID) DESC LIMIT 5")
    stats['distinct_buyers'] = cursor.fetchall()

    conn.close()
    return render_template('statistics.html', stats=stats)

@app.route('/max-basket-total', methods=['POST'])
def max_basket_total():
    start = request.form['start_date']
    end = request.form['end_date']
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT CardNumber, MAX(TotalAmount) FROM Payments
        JOIN Transactions ON Payments.TransactionID = Transactions.TransactionID
        WHERE DATE(Transactions.TransactionID) BETWEEN ? AND ?
        GROUP BY CardNumber
    ''', (start, end))
    results = cursor.fetchall()
    conn.close()

    return render_template('max_basket_total.html', start=start, end=end, results=results)

@app.route('/avg-product-price', methods=['POST'])
def avg_product_price():
    start = request.form['start_date']
    end = request.form['end_date']
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.ProductType, AVG(
            CASE
                WHEN c.Status IN ('Gold', 'Platinum') AND o.OfferPrice IS NOT NULL THEN o.OfferPrice
                ELSE p.RecommendedPrice
            END
        ) AS AvgPrice
        FROM BasketItems bi
        JOIN ShoppingBaskets sb ON bi.BasketID = sb.BasketID
        JOIN Customers c ON sb.CustomerID = c.CustomerID
        JOIN Products p ON bi.ProductID = p.ProductID
        LEFT JOIN Offers o ON o.ProductID = p.ProductID
        JOIN Transactions t ON sb.BasketID = t.BasketID
        WHERE DATE(t.TransactionID) BETWEEN ? AND ?
        GROUP BY p.ProductType
    ''', (start, end))
    results = cursor.fetchall()
    conn.close()

    return render_template('avg_product_price.html', start=start, end=end, results=results)

# --- Main ---
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
