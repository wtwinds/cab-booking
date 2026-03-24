from flask import Flask, render_template, request, redirect, flash, session
from pymongo import MongoClient
import bcrypt
# import random
# from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import MONGO_URI, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

client = MongoClient(MONGO_URI)
db = client['cab_booking']
users = db['users']
rides=db['rides']


# ---------- SELECT CAR PAGE ----------
@app.route('/select-car', methods=['POST'])
def select_car():
    if 'user' not in session:
        return redirect('/')
    
    if request.method!='POST':
        return redirect('/fixed-ride')

    # Form data save temporarily (session)
    session['ride'] = {
        "pickup": request.form['pickup'],
        "destination": request.form['destination'],
        "date": request.form['date'],
        "time": request.form['time']
    }

    return render_template("select_car.html")

#--------Book/car------
@app.route('/book/<car_type>', methods=['POST'])
def book_ride(car_type):
    if 'user' not in session:
        return redirect('/')

    ride = session.get('ride')

    fare = {
        "sedan": 400,
        "suv": 600,
        "electric": 500,
        "mini": 375
    }

    driver = {
        "name": "Rahul Sharma",
        "phone": "9876536780",
        "vehicle": "MH12AB123"
    }

    ride_data = {
        "user": session['user'],
        "pickup": ride['pickup'],
        "destination": ride['destination'],
        "date": ride['date'],
        "time": ride['time'],
        "car": car_type,
        "price": fare.get(car_type),
        "driver": driver,
        "status": "ongoing"
    }

    # ✅ SAVE IN DB
    rides.insert_one(ride_data)

    # ✅ REDIRECT (NO DUPLICATE)
    return redirect(f'/live/{car_type}')

#----------Live---------
@app.route('/live/<car_type>')
def live_page(car_type):
    if 'user' not in session:
        return redirect('/')

    ride = session.get('ride')

    driver = {
        "name": "Rahul Sharma",
        "phone": "9876536780",
        "vehicle": "MH12AB123"
    }

    fare = {
        "sedan": 400,
        "suv": 600,
        "electric": 500,
        "mini": 375
    }

    return render_template("live_ride.html",
        ride=ride,
        driver=driver,
        car=car_type,
        price=fare.get(car_type)
    )

#-------------Cancel/Completed---------
@app.route('/cancel')
def cancel_ride():
    rides.update_one(
        {"user": session['user'], "status": "ongoing"},
        {"$set": {"status": "cancelled"}}
    )
    return redirect('/dashboard')


@app.route('/complete')
def complete_ride():
    rides.update_one(
        {"user": session['user'], "status": "ongoing"},
        {"$set": {"status": "completed"}}
    )
    return redirect('/dashboard')

# ---------- LOGIN ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users.find_one({"email": email})

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
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Password match check
        if password != confirm_password:
            flash("Passwords do not match")
            return redirect('/register')

        # Check if user exists
        if users.find_one({"email": email}):
            flash("User already exists!!")
            return redirect('/register')

        # Save directly in DB
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        users.insert_one({
            "name": name,
            "email": email,
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

# ---------- FIXED RIDE PAGE ----------
@app.route('/fixed-ride')
def fixed_ride():
    if 'user' not in session:
        return redirect('/')
    return render_template("fixed_ride.html")


# ---------- SPOT RIDE PAGE ----------
@app.route('/spot-ride')
def spot_ride():
    if 'user' not in session:
        return redirect('/')
    return render_template("spot_ride.html")

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)