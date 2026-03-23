from flask import Flask, render_template, request, redirect, flash, session
from pymongo import MongoClient
import bcrypt
from config import MONGO_URI, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

client = MongoClient(MONGO_URI)
db = client['cab_booking']
users = db['users']


# ---------- LOGIN ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        password = request.form['password']

        user = users.find_one({"emp_id": emp_id})

        if user and bcrypt.checkpw(password.encode(), user['password']):
            session['user'] = user['name']
            return redirect('/dashboard')
        else:
            flash("Invalid ID or Password")

    return render_template("login.html")


# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        emp_id = request.form['emp_id']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Password match check
        if password != confirm_password:
            flash("Passwords do not match")
            return redirect('/register')

        # Check if user exists
        if users.find_one({"emp_id": emp_id}):
            flash("User already exists!!")
            return redirect('/register')

        # Save directly in DB
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        users.insert_one({
            "name": name,
            "emp_id": emp_id,
            "phone": phone,
            "password": hashed_pw
        })

        session['user'] = name   
        flash("Registration Successful ✅")
        return redirect('/dashboard')

    return render_template("register.html")


# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template("dashboard.html", user=session['user'])


# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)