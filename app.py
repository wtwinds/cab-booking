from flask import Flask, render_template, request, redirect, flash, session
from pymongo import MongoClient
import bcrypt
from config import MONGO_URI, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

client = MongoClient(MONGO_URI)
db = client['cab_booking']
users = db['users']
rides = db['rides']
profiles=db['profiles']

# 🔥 DRIVER DATA
drivers = {
    "sedan": {
        "name": "Rahul Sharma",
        "age": 32,
        "phone": "9876543210",
        "experience": "6 years",
        "id": "DRV10245",
        "trips": 1850,
        "license": "MH12-2020-9876543",
        "vehicle": "MH12AB1234",
        "type": "Sedan"
    },
    "suv": {
        "name": "Amit Verma",
        "age": 38,
        "phone": "9123456780",
        "experience": "10 years",
        "id": "DRV20456",
        "trips": 2450,
        "license": "MH14-2015-4567891",
        "vehicle": "MH14XY5678",
        "type": "SUV"
    },
    "mini": {
        "name": "Neha Patel",
        "age": 27,
        "phone": "9988776655",
        "experience": "3 years",
        "id": "DRV30987",
        "trips": 980,
        "license": "MH02-2021-1122334",
        "vehicle": "MH02CD4321",
        "type": "Mini"
    },
    "electric": {
        "name": "Arjun Mehta",
        "age": 30,
        "phone": "9012345678",
        "experience": "5 years",
        "id": "DRV41562",
        "trips": 1320,
        "license": "MH01-2018-7788990",
        "vehicle": "MH01EV2025",
        "type": "Electric"
    }
}

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
            flash("Invalid Email or Password")

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

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect('/register')

        if users.find_one({"email": email}):
            flash("User already exists!!")
            return redirect('/register')

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

# ---------- SPOT RIDE PAGE ----------
@app.route('/spot-ride')
def spot_ride():
    if 'user' not in session:
        return redirect('/')
    return render_template("spot_ride.html")

# ---------- SELECT CAR ----------
@app.route('/select-car', methods=['POST'])
def select_car():
    if 'user' not in session:
        return redirect('/')

    session['ride'] = {
        "pickup": request.form['pickup'],
        "destination": request.form['destination'],
        "date": request.form['date'],
        "time": request.form['time']
    }

    return render_template("select_car.html")

# ---------- BOOK RIDE ----------
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

    driver = drivers.get(car_type)

    ride_data = {
        "user": session['user'],
        "pickup": ride['pickup'],
        "destination": ride['destination'],
        "date": ride['date'],
        "time": ride['time'],
        "car": car_type,
        "price": fare.get(car_type),
        "driver": driver,
        "status": "ongoing",
        "type": ride.get("ride_type", "spot")
    }

    rides.insert_one(ride_data)

    return redirect(f'/live/{car_type}')

# ---------- LIVE PAGE ----------
@app.route('/live/<car_type>')
def live_page(car_type):
    if 'user' not in session:
        return redirect('/')

    ride = session.get('ride')
    driver = drivers.get(car_type)

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

# ---------- CANCEL PAGE ----------
@app.route('/cancel-page')
def cancel_page():
    if 'user' not in session:
        return redirect('/')
    return render_template("cancel_ride.html")


# ---------- CONFIRM CANCEL ----------
@app.route('/cancel-confirm', methods=['POST'])
def cancel_confirm():
    if 'user' not in session:
        return redirect('/')

    reason = request.form.get('reason')
    comment = request.form.get('comment')

    # ✅ latest ride find karo
    latest_ride = rides.find_one(
        {"user": session['user'], "status": "ongoing"},
        sort=[("_id", -1)]
    )

    if latest_ride:
        rides.update_one(
            {"_id": latest_ride["_id"]},
            {
                "$set": {
                    "status": "cancelled",
                    "cancel_reason": reason,
                    "cancel_comment": comment
                }
            }
        )

    flash("Ride Cancelled Successfully")
    return redirect('/dashboard')

# ---------- COMPLETE ----------
@app.route('/complete')
def complete_ride():
    if 'user' not in session:
        return redirect('/')

    latest_ride = rides.find_one(
        {"user": session['user'], "status": "ongoing"},
        sort=[("_id", -1)]
    )

    if latest_ride:
        rides.update_one(
            {"_id": latest_ride["_id"]},
            {"$set": {"status": "completed"}}
        )

    return redirect('/rating')

#--Rating-----------
@app.route('/rating')
def rating_page():
    if 'user' not in session:
        return redirect('/')
    return render_template("rating.html")

#-----------Save rating---------
@app.route('/submit-rating', methods=['POST'])
def submit_rating():
    rating = request.form.get('rating')
    feedback = request.form.get('feedback')

    latest_ride = rides.find_one(
        {"user": session['user'], "status": "completed"},
        sort=[("_id", -1)]
    )

    if latest_ride:
        rides.update_one(
            {"_id": latest_ride["_id"]},
            {
                "$set": {
                    "rating": rating,
                    "feedback": feedback
                }
            }
        )

    flash("Thanks for your feedback")
    return redirect('/dashboard')

#---History--------------------
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/')

    user_rides = list(rides.find(
        {"user": session['user']}
    ).sort("_id", -1))   # latest first

    return render_template("history.html", rides=user_rides)

#---------------Delete--------
@app.route('/delete-ride/<ride_id>')
def delete_ride(ride_id):
    if 'user' not in session:
        return redirect('/')

    from bson.objectid import ObjectId

    rides.delete_one({"_id": ObjectId(ride_id)})

    flash("Ride deleted successfully")
    return redirect('/history')

# ---------- PROFILE PAGE ----------
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect('/')

    user_profile = profiles.find_one({"user": session['user']}) or {}
    return render_template("profile.html", user=user_profile)


# ---------- SAVE PROFILE ----------
@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return redirect('/')

    profiles.update_one(
        {"user": session['user']},
        {
            "$set": {
                "user": session['user'],
                "full_name": request.form.get("full_name"),
                "employee_id": request.form.get("employee_id"),
                "phone": request.form.get("phone"),
                "department": request.form.get("department"),
                "home_address": request.form.get("home_address"),
                "office_address": request.form.get("office_address")
            }
        },
        upsert=True
    )

    flash("Profile Updated")
    return redirect('/dashboard')

# ---------- FIXED RIDE PAGE ----------
@app.route('/fixed-ride')
def fixed_ride():
    if 'user' not in session:
        return redirect('/')

    return render_template("fixed_ride.html")

# ---------- FIXED RIDE CHECK ----------
@app.route('/fixed-ride-check', methods=['POST'])
def fixed_ride_check():
    if 'user' not in session:
        return redirect('/')

    user_profile = profiles.find_one({"user": session['user']})

    # profile not filled
    if not user_profile or not user_profile.get("home_address") or not user_profile.get("office_address"):
        flash("⚠ Please complete your profile first!")
        return redirect('/profile')

    pickup_type = request.form['pickup']
    destination_type = request.form['destination']

    pickup = user_profile.get("home_address") if pickup_type == "home" else user_profile.get("office_address")
    destination = user_profile.get("home_address") if destination_type == "home" else user_profile.get("office_address")

    session['ride'] = {
        "pickup": pickup,
        "destination": destination,
        "date": request.form['date'],
        "time": request.form['time'],
        "ride_type": "fixed"  
    }

    return render_template("select_car.html")

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)