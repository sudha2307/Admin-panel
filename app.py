import calendar
import psycopg2
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, request, redirect, send_file, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'import calendar
import psycopg2
from io import BytesIO
from datetime import datetime
from flask import Flask, jsonify, render_template, request, redirect, send_file, url_for, flash, session,jsonify
from flask_cors import CORS




app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE_URL = "postgresql://tech-admin_owner:Qc4HOn7Fwuod@ep-cool-frog-a1g7skml.ap-southeast-1.aws.neon.tech/tech-admin?sslmode=require"

# Dummy user credentials
users = {
    "m.sudha23ss@gmail.com": {"password": "sudha@23", "name": "Sudha", "photo": "sudha.jpg"},
    "hellotechdoctors@gmail.com": {"password": "#it151746", "name": "Tech Doctor", "photo": "TD Admins.jpg"},
    "sufiyansac@gmail.com": {"password": "0717", "name": "Sufiyan", "photo": "Sufiyan.jpg"},
    "harees12@gmail.com": {"password": "#harees1212", "name": "Harees", "photo": "al harees.jpg"}
}

# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        dbname="tech-admin",
        user="tech-admin_owner",
        password="Qc4HOn7Fwuod",
        host="ep-cool-frog-a1g7skml.ap-southeast-1.aws.neon.tech",
        port="5432",
        sslmode="require"
    )
    return conn
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['POST'])
def login():
    data = request.json  # Parse JSON data sent by Flutter
    email = data.get('email')
    password = data.get('password')

    # Authenticate the user
    if email in users and users[email]['password'] == password:
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "name": users[email]['name'],
            "photo": users[email]['photo']
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": "Invalid email or password"
        }), 401

            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Set session variables
    username = session['username']
    userphoto = session['userphoto']
    
    # Database connection
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get total balance (total income - total expense)
    cur.execute("SELECT SUM(income) - SUM(expense) FROM accounts")
    total_balance = cur.fetchone()[0] or 0

    # Get current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_month_name = calendar.month_name[current_month]
    
    # Get total income for the current month
    cur.execute("""
        SELECT SUM(income) FROM accounts 
        WHERE EXTRACT(MONTH FROM date) = %s AND EXTRACT(YEAR FROM date) = %s
    """, (current_month, current_year))
    total_income = cur.fetchone()[0] or 0

    # Get total expense for the current month
    cur.execute("""
        SELECT SUM(expense) FROM accounts 
        WHERE EXTRACT(MONTH FROM date) = %s AND EXTRACT(YEAR FROM date) = %s
    """, (current_month, current_year))
    total_expense = cur.fetchone()[0] or 0

    # Prepare monthly income data for bar chart
    monthly_income = [0] * 12
    cur.execute("""
        SELECT EXTRACT(MONTH FROM date) AS month, SUM(income)
        FROM accounts
        WHERE EXTRACT(YEAR FROM date) = %s
        GROUP BY month
        ORDER BY month
    """, (current_year,))
    for row in cur.fetchall():
        month_index = int(row[0]) - 1
        monthly_income[month_index] = row[1]

    # Calculate income and expense percentages for pie chart
    if total_income + total_expense > 0:
        income_percentage = (total_income / (total_income + total_expense)) * 100
        expense_percentage = (total_expense / (total_income + total_expense)) * 100
    else:
        income_percentage = expense_percentage = 0

    # Close database connection
    cur.close()
    conn.close()
    print(f"User photo path: {userphoto}")


    # Render dashboard with data
    return render_template('dashboard.html',
                           username=username,
                           userphoto=userphoto,
                           current_balance=total_balance,
                           current_month_name=current_month_name,
                           total_income=total_income,
                           total_expense=total_expense,
                           monthly_income_data=monthly_income,
                           income_percentage=income_percentage,
                           expense_percentage=expense_percentage)

@app.route('/admin')
def admin():
    if 'username' in session:
        username = session['username']
        userphoto = session['userphoto']
        
        # Fetch projects from the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, due_date FROM projects")
        projects = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('admin.html', username=username, projects=projects,userphoto=userphoto)
    else:
        return redirect(url_for('login'))

# Route to display all project details in a table
@app.route('/projects')
def projects():
     
    conn = get_db_connection()
    cursor = conn.cursor()
    if 'username' in session:
        username = session['username']
        userphoto = session['userphoto']
    
    

    # Fetch all project details
    cursor.execute("SELECT id, name, due_date, status, submitted_date, amount_paid FROM projects ORDER BY id ASC")
    project_data = cursor.fetchall()

    # Count the number of current and completed projects
    cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'upcoming'")
    current_projects_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'completed'")
    completed_projects_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template('projects.html', 
                           projects=project_data, 
                           current_projects_count=current_projects_count, 
                           completed_projects_count=completed_projects_count,username=username,
                           userphoto=userphoto)

@app.route('/invoices')
def invoices():
    if 'username' in session:
        userphoto = session['userphoto']
        conn = get_db_connection()
        cursor = conn.cursor()
        # Fetch projects sorted by ID in ascending order
        cursor.execute("SELECT id, name, submitted_date, invoice FROM projects ORDER BY id ASC")
        projects = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('invoices.html', projects=projects,userphoto=userphoto)
    else:
        return redirect(url_for('login'))

@app.route('/upload_invoice/<int:project_id>', methods=['POST'])
def upload_invoice(project_id):
    if 'username' in session and 'invoice' in request.files:
        invoice_file = request.files['invoice']
        if invoice_file.filename != '':
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Store the invoice PDF as binary data in the database
            cursor.execute("UPDATE projects SET invoice = %s WHERE id = %s", (invoice_file.read(), project_id))
            conn.commit()
            
            cursor.close()
            conn.close()
            flash('Invoice uploaded successfully', 'success')
        else:
            flash('No file selected', 'danger')
    return redirect(url_for('invoices'))

@app.route('/download_invoice/<int:project_id>')
def download_invoice(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch the invoice PDF from the database
    cursor.execute("SELECT invoice FROM projects WHERE id = %s", (project_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result and result[0]:
        return send_file(BytesIO(result[0]), as_attachment=True, download_name=f"invoice_{project_id}.pdf", mimetype='application/pdf')
    else:
        flash("No invoice found for this project.", "danger")
        return redirect(url_for('invoices'))
from datetime import date

@app.route('/add_project', methods=['POST'])
def add_project():
    project_name = request.form['project_name']
    
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert the new project with a placeholder for `due_date` (e.g., today's date or NULL)
    cursor.execute(
        "INSERT INTO projects (name, due_date, status) VALUES (%s, %s, %s)", 
        (project_name, None, 'upcoming')
    )
    
    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()
    
    # Flash success message and redirect to the projects page
    flash('Project added successfully!', 'success')
    return redirect(url_for('projects'))

def get_monthly_data(year, month):
    conn = psycopg2.connect(...)
    cursor = conn.cursor()
    
    # Select records for the specified month
    cursor.execute("""
        SELECT description, 
               CASE WHEN type = 'income' THEN amount ELSE 0 END AS income,
               CASE WHEN type = 'expense' THEN amount ELSE 0 END AS expense
        FROM transactions
        WHERE EXTRACT(YEAR FROM transaction_date) = %s
          AND EXTRACT(MONTH FROM transaction_date) = %s
    """, (year, month))
    
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return records
@app.route('/accounts', methods=['GET', 'POST'])
def accounts():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Initialize selected year and month to current values
    current_date = datetime.now()
    selected_year = current_date.year
    selected_month = current_date.month
    userphoto = session['userphoto']

    # Update selected month and year if specified in the form
    if request.method == 'POST':
        selected_year = int(request.form.get('year', selected_year))
        selected_month = int(request.form.get('month', selected_month))

    # Fetch records for the specified month and year, including the date column
    cursor.execute("""
        SELECT description, COALESCE(income, 0) AS income, COALESCE(expense, 0) AS expense, date
        FROM accounts
        WHERE EXTRACT(YEAR FROM date) = %s AND EXTRACT(MONTH FROM date) = %s
        ORDER BY date ASC
    """, (selected_year, selected_month))
    current_month_records = cursor.fetchall()

    # Calculate the current month income and expense totals
    total_income = sum(record[1] for record in current_month_records)
    total_expense = sum(record[2] for record in current_month_records)

    # Query to get the total income and expense across all records
    cursor.execute("""
        SELECT COALESCE(SUM(income), 0) AS total_income, COALESCE(SUM(expense), 0) AS total_expense
        FROM accounts
    """)
    total_income_all, total_expense_all = cursor.fetchone()
    total_balance = total_income_all - total_expense_all

    month_name_dict = {i: calendar.month_name[i] for i in range(1, 13)}

    # Close the database connection
    cursor.close()
    conn.close()

    # Render the template with updated values
    return render_template(
        'accounts.html',
        current_balance=total_balance,  # Total balance from all transactions
        total_income=total_income,       # Current month income
        total_expense=total_expense,     # Current month expense
        current_month_name=calendar.month_name[selected_month],
        current_month_records=current_month_records,
        month_name_dict=month_name_dict,  # Pass the dictionary to the template
        selected_month=selected_month,    # Current month selection for the dropdown
        selected_year=selected_year,
        userphoto=userphoto      # Current year selection for the dropdown
    )

# Route for adding a new expense with date
@app.route('/add_expense', methods=['POST'])
def add_expense():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get form data
    description = request.form['expense_description']
    amount = request.form['expense_amount']
    date_str = request.form['expense_date']
    expense_date = datetime.strptime(date_str, '%Y-%m-%d')  # Convert string to date

    # Insert new expense record
    cursor.execute("""
        INSERT INTO accounts (description, expense, date)
        VALUES (%s, %s, %s)
    """, (description, amount, expense_date))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('accounts'))


# Function to end the month and transfer data to monthly_accounts table
def end_month():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Transfer current month data to monthly_accounts table
    cursor.execute("""
        INSERT INTO monthly_accounts (year, month, month_name, income, expense)
        SELECT EXTRACT(YEAR FROM CURRENT_DATE), EXTRACT(MONTH FROM CURRENT_DATE), %s, 
               COALESCE(SUM(income), 0), COALESCE(SUM(expense), 0)
        FROM accounts
    """, (month_name[current_month],))
    
    # Clear current month's data but retain balance
    cursor.execute("DELETE FROM accounts")
    conn.commit()
    cursor.close()
    conn.close()



# Modify the complete_project route to add income to accounts

@app.route('/complete_project/<int:project_id>', methods=['POST'])
def complete_project(project_id):
    # Get form data with date parsing
    try:
        submitted_date = datetime.strptime(request.form['submitted_date'], '%Y-%m-%d').date()
        due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
        amount_paid = float(request.form['amount_paid'])
    except ValueError:
        # Handle invalid date or amount formats
        flash("Invalid date or amount format.", "error")
        return redirect(url_for('projects'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Update project status to completed
        cursor.execute("""
            UPDATE projects 
            SET status = 'completed', submitted_date = %s, due_date = %s, amount_paid = %s 
            WHERE id = %s
        """, (submitted_date, due_date, amount_paid, project_id))
        
        # Insert income record into accounts with date for tracking
        cursor.execute("""
            INSERT INTO accounts (description, income, date) 
            VALUES (%s, %s, %s)
        """, (f"Income from project ID {project_id}", amount_paid, submitted_date))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"Error completing project: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()

    flash("Project marked as completed and income recorded.", "success")
    return redirect(url_for('projects'))
    
CORS(app)

if __name__ == '__main__':
    app.run(debug=True)


DATABASE_URL = "postgresql://tech-admin_owner:Qc4HOn7Fwuod@ep-cool-frog-a1g7skml.ap-southeast-1.aws.neon.tech/tech-admin?sslmode=require"

# Dummy user credentials
users = {
    "m.sudha23ss@gmail.com": {"password": "sudha@23", "name": "Sudha", "photo": "sudha.jpg"},
    "hellotechdoctors@gmail.com": {"password": "#it151746", "name": "Tech Doctor", "photo": "TD Admins.jpg"},
    "sufiyansac@gmail.com": {"password": "0717", "name": "Sufiyan", "photo": "Sufiyan.jpg"},
    "alharees960@gmail.com": {"password": "#harees1212", "name": "Harees", "photo": "al harees.jpg"}
}

# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        dbname="tech-admin",
        user="tech-admin_owner",
        password="Qc4HOn7Fwuod",
        host="ep-cool-frog-a1g7skml.ap-southeast-1.aws.neon.tech",
        port="5432",
        sslmode="require"
    )
    return conn
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Authenticate the user
        if email in users and users[email]['password'] == password:
            session['username'] = users[email]['name']
            session['userphoto'] = users[email]['photo']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Set session variables
    username = session['username']
    userphoto = session['userphoto']
    
    # Database connection
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get total balance (total income - total expense)
    cur.execute("SELECT SUM(income) - SUM(expense) FROM accounts")
    total_balance = cur.fetchone()[0] or 0

    # Get current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_month_name = calendar.month_name[current_month]
    
    # Get total income for the current month
    cur.execute("""
        SELECT SUM(income) FROM accounts 
        WHERE EXTRACT(MONTH FROM date) = %s AND EXTRACT(YEAR FROM date) = %s
    """, (current_month, current_year))
    total_income = cur.fetchone()[0] or 0

    # Get total expense for the current month
    cur.execute("""
        SELECT SUM(expense) FROM accounts 
        WHERE EXTRACT(MONTH FROM date) = %s AND EXTRACT(YEAR FROM date) = %s
    """, (current_month, current_year))
    total_expense = cur.fetchone()[0] or 0

    # Prepare monthly income data for bar chart
    monthly_income = [0] * 12
    cur.execute("""
        SELECT EXTRACT(MONTH FROM date) AS month, SUM(income)
        FROM accounts
        WHERE EXTRACT(YEAR FROM date) = %s
        GROUP BY month
        ORDER BY month
    """, (current_year,))
    for row in cur.fetchall():
        month_index = int(row[0]) - 1
        monthly_income[month_index] = row[1]

    # Calculate income and expense percentages for pie chart
    if total_income + total_expense > 0:
        income_percentage = (total_income / (total_income + total_expense)) * 100
        expense_percentage = (total_expense / (total_income + total_expense)) * 100
    else:
        income_percentage = expense_percentage = 0

    # Close database connection
    cur.close()
    conn.close()
    print(f"User photo path: {userphoto}")


    # Render dashboard with data
    return render_template('dashboard.html',
                           username=username,
                           userphoto=userphoto,
                           current_balance=total_balance,
                           current_month_name=current_month_name,
                           total_income=total_income,
                           total_expense=total_expense,
                           monthly_income_data=monthly_income,
                           income_percentage=income_percentage,
                           expense_percentage=expense_percentage)

@app.route('/admin')
def admin():
    if 'username' in session:
        username = session['username']
        userphoto = session['userphoto']
        
        # Fetch projects from the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, due_date FROM projects")
        projects = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('admin.html', username=username, projects=projects,userphoto=userphoto)
    else:
        return redirect(url_for('login'))

# Route to display all project details in a table
@app.route('/projects')
def projects():
     
    conn = get_db_connection()
    cursor = conn.cursor()
    if 'username' in session:
        username = session['username']
        userphoto = session['userphoto']
    
    

    # Fetch all project details
    cursor.execute("SELECT id, name, due_date, status, submitted_date, amount_paid FROM projects ORDER BY id ASC")
    project_data = cursor.fetchall()

    # Count the number of current and completed projects
    cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'upcoming'")
    current_projects_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'completed'")
    completed_projects_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template('projects.html', 
                           projects=project_data, 
                           current_projects_count=current_projects_count, 
                           completed_projects_count=completed_projects_count,username=username,
                           userphoto=userphoto)

@app.route('/invoices')
def invoices():
    if 'username' in session:
        userphoto = session['userphoto']
        conn = get_db_connection()
        cursor = conn.cursor()
        # Fetch projects sorted by ID in ascending order
        cursor.execute("SELECT id, name, submitted_date, invoice FROM projects ORDER BY id ASC")
        projects = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('invoices.html', projects=projects,userphoto=userphoto)
    else:
        return redirect(url_for('login'))

@app.route('/upload_invoice/<int:project_id>', methods=['POST'])
def upload_invoice(project_id):
    if 'username' in session and 'invoice' in request.files:
        invoice_file = request.files['invoice']
        if invoice_file.filename != '':
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Store the invoice PDF as binary data in the database
            cursor.execute("UPDATE projects SET invoice = %s WHERE id = %s", (invoice_file.read(), project_id))
            conn.commit()
            
            cursor.close()
            conn.close()
            flash('Invoice uploaded successfully', 'success')
        else:
            flash('No file selected', 'danger')
    return redirect(url_for('invoices'))

@app.route('/download_invoice/<int:project_id>')
def download_invoice(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch the invoice PDF from the database
    cursor.execute("SELECT invoice FROM projects WHERE id = %s", (project_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result and result[0]:
        return send_file(BytesIO(result[0]), as_attachment=True, download_name=f"invoice_{project_id}.pdf", mimetype='application/pdf')
    else:
        flash("No invoice found for this project.", "danger")
        return redirect(url_for('invoices'))
from datetime import date

@app.route('/add_project', methods=['POST'])
def add_project():
    project_name = request.form['project_name']
    
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert the new project with a placeholder for `due_date` (e.g., today's date or NULL)
    cursor.execute(
        "INSERT INTO projects (name, due_date, status) VALUES (%s, %s, %s)", 
        (project_name, None, 'upcoming')
    )
    
    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()
    
    # Flash success message and redirect to the projects page
    flash('Project added successfully!', 'success')
    return redirect(url_for('projects'))

def get_monthly_data(year, month):
    conn = psycopg2.connect(...)
    cursor = conn.cursor()
    
    # Select records for the specified month
    cursor.execute("""
        SELECT description, 
               CASE WHEN type = 'income' THEN amount ELSE 0 END AS income,
               CASE WHEN type = 'expense' THEN amount ELSE 0 END AS expense
        FROM transactions
        WHERE EXTRACT(YEAR FROM transaction_date) = %s
          AND EXTRACT(MONTH FROM transaction_date) = %s
    """, (year, month))
    
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return records
@app.route('/accounts', methods=['GET', 'POST'])
def accounts():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Initialize selected year and month to current values
    current_date = datetime.now()
    selected_year = current_date.year
    selected_month = current_date.month
    userphoto = session['userphoto']

    # Update selected month and year if specified in the form
    if request.method == 'POST':
        selected_year = int(request.form.get('year', selected_year))
        selected_month = int(request.form.get('month', selected_month))

    # Fetch records for the specified month and year, including the date column
    cursor.execute("""
        SELECT description, COALESCE(income, 0) AS income, COALESCE(expense, 0) AS expense, date
        FROM accounts
        WHERE EXTRACT(YEAR FROM date) = %s AND EXTRACT(MONTH FROM date) = %s
        ORDER BY date ASC
    """, (selected_year, selected_month))
    current_month_records = cursor.fetchall()

    # Calculate the current month income and expense totals
    total_income = sum(record[1] for record in current_month_records)
    total_expense = sum(record[2] for record in current_month_records)

    # Query to get the total income and expense across all records
    cursor.execute("""
        SELECT COALESCE(SUM(income), 0) AS total_income, COALESCE(SUM(expense), 0) AS total_expense
        FROM accounts
    """)
    total_income_all, total_expense_all = cursor.fetchone()
    total_balance = total_income_all - total_expense_all

    month_name_dict = {i: calendar.month_name[i] for i in range(1, 13)}

    # Close the database connection
    cursor.close()
    conn.close()

    # Render the template with updated values
    return render_template(
        'accounts.html',
        current_balance=total_balance,  # Total balance from all transactions
        total_income=total_income,       # Current month income
        total_expense=total_expense,     # Current month expense
        current_month_name=calendar.month_name[selected_month],
        current_month_records=current_month_records,
        month_name_dict=month_name_dict,  # Pass the dictionary to the template
        selected_month=selected_month,    # Current month selection for the dropdown
        selected_year=selected_year,
        userphoto=userphoto      # Current year selection for the dropdown
    )

# Route for adding a new expense with date
@app.route('/add_expense', methods=['POST'])
def add_expense():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get form data
    description = request.form['expense_description']
    amount = request.form['expense_amount']
    date_str = request.form['expense_date']
    expense_date = datetime.strptime(date_str, '%Y-%m-%d')  # Convert string to date

    # Insert new expense record
    cursor.execute("""
        INSERT INTO accounts (description, expense, date)
        VALUES (%s, %s, %s)
    """, (description, amount, expense_date))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('accounts'))


# Function to end the month and transfer data to monthly_accounts table
def end_month():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Transfer current month data to monthly_accounts table
    cursor.execute("""
        INSERT INTO monthly_accounts (year, month, month_name, income, expense)
        SELECT EXTRACT(YEAR FROM CURRENT_DATE), EXTRACT(MONTH FROM CURRENT_DATE), %s, 
               COALESCE(SUM(income), 0), COALESCE(SUM(expense), 0)
        FROM accounts
    """, (month_name[current_month],))
    
    # Clear current month's data but retain balance
    cursor.execute("DELETE FROM accounts")
    conn.commit()
    cursor.close()
    conn.close()



# Modify the complete_project route to add income to accounts

@app.route('/complete_project/<int:project_id>', methods=['POST'])
def complete_project(project_id):
    # Get form data with date parsing
    try:
        submitted_date = datetime.strptime(request.form['submitted_date'], '%Y-%m-%d').date()
        due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
        amount_paid = float(request.form['amount_paid'])
    except ValueError:
        # Handle invalid date or amount formats
        flash("Invalid date or amount format.", "error")
        return redirect(url_for('projects'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Update project status to completed
        cursor.execute("""
            UPDATE projects 
            SET status = 'completed', submitted_date = %s, due_date = %s, amount_paid = %s 
            WHERE id = %s
        """, (submitted_date, due_date, amount_paid, project_id))
        
        # Insert income record into accounts with date for tracking
        cursor.execute("""
            INSERT INTO accounts (description, income, date) 
            VALUES (%s, %s, %s)
        """, (f"Income from project ID {project_id}", amount_paid, submitted_date))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"Error completing project: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()

    flash("Project marked as completed and income recorded.", "success")
    return redirect(url_for('projects'))

if __name__ == '__main__':
    app.run(debug=True)
