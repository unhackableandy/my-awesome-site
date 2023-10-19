import time
from flask import Flask, render_template, redirect, url_for, session, flash, request
from werkzeug.security import check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
import os
import subprocess
import psutil
from dotenv import load_dotenv

load_dotenv()

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key_here"
app.config["SESSION_TYPE"] = "filesystem"


class LoginForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class DashboardForm(FlaskForm):
    command = StringField(
        "Enter command to reset server:",
        validators=[DataRequired()],
        default="shutdown -r",
    )
    submit = SubmitField("Submit")


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if (
            form.username.data == ADMIN_USERNAME
            and form.password.data == ADMIN_PASSWORD
        ):
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            flash("Login Unsuccessful. Please check username and password", "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    # Server stats
    cpu_percent = psutil.cpu_percent()
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage("/")
    uptime = int(time.time() - psutil.boot_time())

    form = DashboardForm()

    stats = {
        "CPU Usage": f"{cpu_percent}%",
        "Memory Usage": f"{memory_info.percent}%",
        "Disk Usage": f"{disk_info.percent}%",
        "Uptime": f"{uptime // 3600}h {(uptime % 3600) // 60}m",
    }

    # If command form is submitted
    output = None
    if form.validate_on_submit():
        command = form.command.data
        try:
            output = subprocess.check_output(command, shell=True).decode("utf-8")
        except Exception as e:
            output = str(e)

    return render_template("dashboard.html", form=form, stats=stats, output=output)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
