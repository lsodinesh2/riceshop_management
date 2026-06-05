from flask import Flask, render_template, request, redirect, session, send_file
from database import get_db
from decimal import Decimal
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table
from io import BytesIO

app = Flask(__name__)
app.secret_key = "rice_shop_secret"

# ======================
# AUTO LOGIN (For Development)
# ======================
@app.before_request
def auto_login():
    if 'user' not in session and request.endpoint not in ['login', 'static']:
        # Auto login as admin (change as needed)
        session['user'] = 'admin'
        session['role'] = 'admin'
        print("🔑 Auto logged in as admin")

# ======================
# HOME
# ======================
@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return redirect('/login')


# ======================
# LOGIN (Kept for future use)
# ======================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM users
            WHERE username=%s AND password=%s
        """, (username, password))

        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user:
            session['user'] = user['username']
            session['role'] = user['role']
            return redirect('/dashboard')

        return render_template('login.html', error="Invalid Login")

    return render_template('login.html')


# Rest of your code remains exactly the same...
# (dashboard, products, customers, billing, create-bill, etc.)
# DASHBOARD
# ======================
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM rice_products")
    products = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM customers")
    customers = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM suppliers")
    suppliers = cursor.fetchone()['total']

    cursor.execute("SELECT IFNULL(SUM(total_amount),0) AS total FROM sales")
    sales = cursor.fetchone()['total']

    cursor.execute("""
        SELECT DATE(sale_date) AS date,
               SUM(total_amount) AS total
        FROM sales
        GROUP BY DATE(sale_date)
        ORDER BY date DESC
        LIMIT 7
    """)
    chart_data = cursor.fetchall()

    cursor.close()
    db.close()

    labels = [str(x['date']) for x in chart_data][::-1]
    values = [float(x['total']) for x in chart_data][::-1]

    return render_template(
        'dashboard.html',
        username=session['user'],
        products=products,
        customers=customers,
        suppliers=suppliers,
        sales=sales,
        chart_labels=labels,
        chart_values=values
    )


# ======================
# PRODUCTS
# ======================
@app.route('/products')
def products():

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM rice_products ORDER BY id DESC")
    data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('products.html', products=data)


@app.route('/add-product', methods=['POST'])
def add_product():

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO rice_products
        (rice_name, category, purchase_price, selling_price, stock_kg, stock_bags)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        request.form['rice_name'],
        request.form['category'],
        request.form['purchase_price'],
        request.form['selling_price'],
        request.form['stock_kg'],
        request.form['stock_bags']
    ))

    db.commit()
    cursor.close()
    db.close()

    return redirect('/products')


@app.route('/delete-product/<int:id>')
def delete_product(id):

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM rice_products WHERE id=%s", (id,))

    db.commit()
    cursor.close()
    db.close()

    return redirect('/products')


@app.route('/edit-product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT * FROM rice_products WHERE id=%s", (id,))
        product = cursor.fetchone()

        cursor.close()
        db.close()

        return render_template('edit_product.html', product=product)

    cursor.execute("""
        UPDATE rice_products
        SET rice_name=%s,
            category=%s,
            purchase_price=%s,
            selling_price=%s,
            stock_kg=%s,
            stock_bags=%s
        WHERE id=%s
    """, (
        request.form['rice_name'],
        request.form['category'],
        request.form['purchase_price'],
        request.form['selling_price'],
        request.form['stock_kg'],
        request.form['stock_bags'],
        id
    ))

    db.commit()
    cursor.close()
    db.close()

    return redirect('/products')


# ======================
# CUSTOMERS
# ======================
@app.route('/customers')
def customers():

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM customers ORDER BY id DESC")
    data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('customers.html', customers=data)


@app.route('/add-customer', methods=['POST'])
def add_customer():

    if 'user' not in session:
        return redirect('/login')

    name = request.form['name']
    phone = request.form['phone']
    address = request.form['address']
    due_amount = request.form.get('due_amount', 0.00)

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO customers(name, phone, address, due_amount)
        VALUES (%s,%s,%s,%s)
    """, (name, phone, address, due_amount))

    db.commit()
    cursor.close()
    db.close()

    return redirect('/customers')


# ======================
@app.route('/delete-customer/<int:id>')
def delete_customer(id):

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM customers WHERE id=%s",
        (id,)
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect('/customers')
# SUPPLIERS
# ======================
@app.route('/suppliers')
def suppliers():

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM suppliers
        ORDER BY id DESC
    """)

    suppliers = cursor.fetchall()

    total_purchase = sum(
        float(s['total_purchase'] or 0)
        for s in suppliers
    )

    total_paid = sum(
        float(s['total_paid'] or 0)
        for s in suppliers
    )

    total_due = sum(
        float(s['due_amount'] or 0)
        for s in suppliers
    )

    cursor.close()
    db.close()

    return render_template(
        "suppliers.html",
        suppliers=suppliers,
        total_purchase=total_purchase,
        total_paid=total_paid,
        total_due=total_due
    )


@app.route('/add-supplier', methods=['POST'])
def add_supplier():

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO suppliers(
            name,
            phone,
            address,
            total_purchase,
            total_paid,
            due_amount
        )
        VALUES(%s,%s,%s,%s,%s,%s)
    """, (
        request.form['name'],
        request.form['phone'],
        request.form['address'],
        request.form.get('total_purchase', 0),
        request.form.get('total_paid', 0),
        float(request.form.get('total_purchase', 0))
        -
        float(request.form.get('total_paid', 0))
    ))

    db.commit()

    cursor.close()
    db.close()

    return redirect('/suppliers')


# ======================
# BILLING
# ======================
@app.route('/billing')
def billing():

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Products
    cursor.execute("SELECT * FROM rice_products")
    products = cursor.fetchall()

    # Customer Ledger Data
    cursor.execute("""
        SELECT
            c.id,
            c.name,
            c.phone,
            COALESCE(SUM(s.total_amount),0) AS total_amount,
            COALESCE(SUM(s.paid_amount),0) AS total_paid
        FROM customers c
        LEFT JOIN sales s
            ON c.id = s.customer_id
        GROUP BY c.id, c.name, c.phone
        ORDER BY c.id DESC
    """)
    customers = cursor.fetchall()

    for c in customers:
        c['remaining'] = float(c['total_amount']) - float(c['total_paid'])

    # Recent Sales
    cursor.execute("""
        SELECT
            s.id,
            s.total_amount,
            s.paid_amount,
            s.sale_date,
            c.name
        FROM sales s
        JOIN customers c
            ON s.customer_id = c.id
        ORDER BY s.id DESC
        LIMIT 10
    """)
    recent_sales = cursor.fetchall()

    for r in recent_sales:
        r['remaining_amount'] = float(r['total_amount']) - float(r['paid_amount'])

    cursor.close()
    db.close()

    return render_template(
        'billing.html',
        products=products,
        customers=customers,
        recent_sales=recent_sales
    )


# ======================
# CREATE BILL
# ======================
@app.route('/create-bill', methods=['POST'])
def create_bill():

    if 'user' not in session:
        return redirect('/login')

    customer_id = request.form['customer_id']
    product_id = request.form['product_id']
    quantity_kg = Decimal(request.form['quantity_kg'])
    paid_amount = Decimal(request.form.get('paid_amount') or "0")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT selling_price
        FROM rice_products
        WHERE id=%s
    """, (product_id,))

    product = cursor.fetchone()

    price = Decimal(product['selling_price'])
    total_amount = price * quantity_kg

    cursor.execute("""
        INSERT INTO sales(customer_id, total_amount, paid_amount, payment_method, sale_date)
        VALUES (%s,%s,%s,%s,NOW())
    """, (customer_id, total_amount, paid_amount, "Cash"))

    sale_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO sale_items(sale_id, product_id, quantity_kg, price)
        VALUES (%s,%s,%s,%s)
    """, (sale_id, product_id, quantity_kg, price))

    cursor.execute("""
        UPDATE rice_products
        SET stock_kg = stock_kg - %s
        WHERE id=%s
    """, (quantity_kg, product_id))

    db.commit()
    cursor.close()
    db.close()

    return redirect(f'/invoice/{sale_id}')


# ======================
# INVOICE
# ======================
@app.route('/invoice/<int:sale_id>')
def invoice(sale_id):

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT s.*, c.name, c.phone, c.address
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        WHERE s.id=%s
    """, (sale_id,))
    sale = cursor.fetchone()

    sale['remaining_amount'] = float(sale['total_amount'] or 0) - float(sale['paid_amount'] or 0)

    cursor.execute("""
        SELECT si.*, p.rice_name
        FROM sale_items si
        JOIN rice_products p ON si.product_id = p.id
        WHERE si.sale_id=%s
    """, (sale_id,))
    items = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('invoice.html', sale=sale, items=items)


# ======================
# ======================
# CUSTOMER LEDGER
# ======================
@app.route('/customer-ledger')
def customer_ledger():

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            c.id,
            c.name,
            c.phone,
            COALESCE(SUM(s.total_amount),0) AS total_amount,
            COALESCE(SUM(s.paid_amount),0) AS total_paid
        FROM customers c
        LEFT JOIN sales s
            ON c.id = s.customer_id
        GROUP BY c.id, c.name, c.phone
        ORDER BY c.id DESC
    """)

    customers = cursor.fetchall()

    total_paid = 0
    total_pending = 0

    for c in customers:
        total_amount = float(c['total_amount'] or 0)
        paid_amount = float(c['total_paid'] or 0)

        c['remaining'] = round(total_amount - paid_amount, 2)

        total_paid += paid_amount
        total_pending += c['remaining']

    print(customers)   # DEBUG

    cursor.close()
    db.close()

    return render_template(
        "customer_ledger.html",
        customers=customers,
        total_paid=total_paid,
        total_pending=total_pending
    )


# ======================
@app.route('/update-supplier-payment', methods=['POST'])
def update_supplier_payment():

    if 'user' not in session:
        return redirect('/login')

    supplier_id = request.form['supplier_id']

    purchase_amount = float(
        request.form.get('purchase_amount') or 0
    )

    paid_amount = float(
        request.form.get('paid_amount') or 0
    )

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            total_purchase,
            total_paid
        FROM suppliers
        WHERE id=%s
    """, (supplier_id,))

    supplier = cursor.fetchone()

    new_purchase = float(
        supplier['total_purchase'] or 0
    ) + purchase_amount

    new_paid = float(
        supplier['total_paid'] or 0
    ) + paid_amount

    new_due = new_purchase - new_paid

    cursor.execute("""
        UPDATE suppliers
        SET
            total_purchase=%s,
            total_paid=%s,
            due_amount=%s
        WHERE id=%s
    """, (
        new_purchase,
        new_paid,
        new_due,
        supplier_id
    ))

    db.commit()

    cursor.close()
    db.close()

    return redirect('/suppliers')
# LOGOUT
# ======================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ======================
# ======================
# DOWNLOAD SUPPLIERS PDF
# ======================
@app.route('/download-suppliers-pdf')
def download_suppliers_pdf():

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM suppliers
        ORDER BY id DESC
    """)

    suppliers = cursor.fetchall()

    cursor.close()
    db.close()

    buffer = BytesIO()

    pdf = SimpleDocTemplate(buffer)

    data = [[
        "ID",
        "Name",
        "Phone",
        "Purchased",
        "Paid",
        "Due"
    ]]

    for s in suppliers:

        data.append([
            s['id'],
            s['name'],
            s['phone'],
            s['total_purchase'],
            s['total_paid'],
            s['due_amount']
        ])

    table = Table(data)

    pdf.build([table])

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="suppliers_report.pdf",
        mimetype="application/pdf"
    )


# ======================
# DOWNLOAD SUPPLIERS EXCEL
# ======================
@app.route('/download-suppliers-excel')
def download_suppliers_excel():

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM suppliers
        ORDER BY id DESC
    """)

    suppliers = cursor.fetchall()

    cursor.close()
    db.close()

    df = pd.DataFrame(suppliers)

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine='openpyxl'
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name='Suppliers'
        )

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="suppliers_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# RUN
# ======================
if __name__ == '__main__':
    app.run(debug=True)