import json

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   url_for)
from flask_login import (LoginManager, UserMixin, login_required, login_user,
                         logout_user)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from api import get_weather_forecast
from config import *

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user is not None and user.check_password(request.form["password"]):
            login_user(user)
            flash("Вы успешно вошли в систему.", "success")
            return redirect(url_for("main_weather"))
        else:
            flash("Неверное имя пользователя или пароль", "danger")
    return render_template("login.html")


@app.route("/main_weather", methods=["GET", "POST"])
@login_required
def main_weather():
    if request.method == "POST":
        city_name = request.form["city"].strip()
        if not city_name:
            flash("Пожалуйста, введите название города", "error")
            return render_template("main_weather.html")

        try:
            result = get_weather_forecast(city_name)
        except Exception as e:
            flash(f"Ошибка при получении прогноза погоды: {e}", "error")
            return render_template("main_weather.html")
        dates = [date.strftime("%Y-%m-%d") for date in result.date]

        temperatures_max = result["temperature_2m_max"].apply(lambda x: f"{int(x)}")
        temperatures_min = result["temperature_2m_min"].apply(lambda x: f"{x:.0f}")
        precipitation = result["precipitation_hours"]
        current_temperature = (
            result["current_temperature_2m"].apply(lambda x: f"{int(x)}").iloc[0]
        )
        current_apparent_temperature = (
            result["current_apparent_temperature"].apply(lambda x: f"{int(x)}").iloc[0]
        )

        return render_template(
            "main_weather.html",
            city_name=city_name,
            dates=dates,
            temperatures_max=temperatures_max,
            temperatures_min=temperatures_min,
            precipitation=precipitation,
            current_temperature=current_temperature,
            current_apparent_temperature=current_apparent_temperature,
        )

    return render_template("main_weather.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("Пользователь с таким именем или email уже существует.", "danger")
            return render_template("register.html")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash(
            "Вы успешно зарегистрированы. Теперь вы можете войти в систему.", "success"
        )
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/cities")
def cities():
    with open("path/to/cities.json", "r", encoding="utf-8") as f:
        cities_data = json.load(f)
    return jsonify(cities_data)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Создает все таблицы, если они не существуют
    app.run(debug=True)
