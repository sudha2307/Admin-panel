from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Dummy user credentials for testing
users = {
    "m.sudha23ss@gmail.com": "sudha@23",
    "hellotechdoctors@gmail.com": "#it151746",
    "sufiyansac@gmail.com": "0717",
    "harees12@gmail.com": "#harees1212"
}

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Authenticate the user
        if email in users and users[email] == password:
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard', username=email.split('@')[0].capitalize()))
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('login.html')

@app.route('/dashboard/<username>')
def dashboard(username):
    return f"Welcome to the dashboard, {username}!"

if __name__ == '__main__':
    app.run(debug=True)
