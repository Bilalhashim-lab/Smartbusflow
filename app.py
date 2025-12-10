from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_mail import Mail, Message
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# --- Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(140), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(140), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    email = db.Column(db.String(140))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- User loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---
@app.route("/")
def index():
    upcoming = [
        {"route": "Route A", "time": "07:30 AM", "eta": "10 min"},
        {"route": "Route B", "time": "08:00 AM", "eta": "25 min"},
    ]
    return render_template("index.html", upcoming=upcoming)

@app.route("/schedule")
def schedule():
    # sample static schedule
    routes = [
        {"route": "Route A", "stops": ["Stop 1", "Stop 2", "Stop 3"], "first": "06:30", "last": "22:00", "freq":"15m"},
        {"route": "Route B", "stops": ["Stop X", "Stop Y"], "first": "07:00", "last": "21:30", "freq":"20m"},
    ]
    return render_template("schedule.html", routes=routes)

@app.route("/track")
def track():
    # mock positions for client simulation
    buses = [
        {"id": "SB-101", "lat": 28.7041, "lng": 77.1025, "route": "Route A"},
        {"id": "SB-202", "lat": 28.7055, "lng": 77.1050, "route": "Route B"},
    ]
    return render_template("track.html", buses=buses)

@app.route("/fare", methods=["GET", "POST"])
def fare():
    result = None
    if request.method == "POST":
        try:
            dist = float(request.form.get("distance", "0"))
            base = 20.0
            per_km = 6.0
            result = max(base, base + dist * per_km)
        except Exception:
            result = "Invalid input"
    return render_template("fare.html", result=result)

@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email")
    if not email:
        flash("Please provide an email", "danger")
        return redirect(url_for("index"))
    if Subscriber.query.filter_by(email=email).first():
        flash("You're already subscribed!", "info")
        return redirect(url_for("index"))
    sub = Subscriber(email=email)
    db.session.add(sub)
    db.session.commit()
    # optional welcome email (if mail is configured)
    try:
        msg = Message("Welcome to SmartBusFlow", recipients=[email])
        msg.body = "Thanks for subscribing to SmartBusFlow newsletter!"
        mail.send(msg)
    except Exception:
        app.logger.info("Mail send failed or not configured.")
    flash("Subscribed successfully! Check your email if configured.", "success")
    return redirect(url_for("index"))

@app.route("/contact", methods=["GET","POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        cm = ContactMessage(name=name, email=email, message=message)
        db.session.add(cm)
        db.session.commit()
        flash("Message sent. We'll get back to you soon.", "success")
        # optionally notify admin
        try:
            admin = app.config.get("MAIL_DEFAULT_SENDER")
            if admin:
                msg = Message("New contact message", recipients=[admin])
                msg.body = f"From: {name} <{email}>\n\n{message}"
                mail.send(msg)
        except Exception:
            app.logger.info("Admin mail notify failed.")
        return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        pw = request.form.get("password")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))
        user = User(name=name, email=email)
        user.set_password(pw)
        db.session.add(user)
        db.session.commit()
        flash("Account created — please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        pw = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(pw):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard") if user.is_admin else url_for("index"))
        flash("Invalid credentials.", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_admin:
        abort(403)
    users = User.query.order_by(User.created_at.desc()).all()
    subscribers = Subscriber.query.order_by(Subscriber.created_at.desc()).all()
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("dashboard.html", users=users, subscribers=subscribers, messages=messages)

# --- CLI helper to create admin and init db ---
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database created (if not exists).")

@app.cli.command("create-admin")
def create_admin():
    email = input("Admin email: ").strip()
    name = input("Admin name: ").strip()
    pw = input("Admin password: ").strip()
    if User.query.filter_by(email=email).first():
        print("User exists.")
        return
    admin = User(name=name, email=email, is_admin=True)
    admin.set_password(pw)
    db.session.add(admin)
    db.session.commit()
    print("Admin created.")

if __name__ == "__main__":
    os.makedirs("instance", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
