from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import csv
from io import StringIO
from flask import Response

app = Flask(__name__)
app.secret_key = "your_secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


with app.app_context():
    db.create_all()

USER_CREDENTIALS = {"username": "admin", "password": "1234"}


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if (
            username == USER_CREDENTIALS["username"]
            and password == USER_CREDENTIALS["password"]
        ):
            session["user"] = username
            flash("Lgin successful", "success")
            return redirect(url_for("show_users"))
        else:
            flash("Invalid credential", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("LOgout successful", "success")
    return redirect(url_for("login"))


@app.route("/users")
def show_users():
    search_term = request.args.get("search", "").strip().lower()
    page = request.args.get("page", 1, type=int)
    per_page = 6
    query = User.query
    if search_term:
        query = query.filter(User.name.ilike(f"%{search_term}%"))
    users_paginated = query.order_by(User.name).paginate(page=page, per_page=per_page)

    return render_template("greet.html", users=users_paginated, search_term=search_term)


@app.route("/", methods=["GET", "POST"])
def home():
    return "App running succesful"
    if "user" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            flash("please enter name", "danger")
        else:
            new_user = User(name=username.title())
            db.session.add(new_user)
            db.session.commit()
            flash("user added successfully", "success")
            return redirect(url_for("show_users"))
    return render_template("index.html")


@app.route("/edit/<int:user_id>", methods=["GET", "POST"])
def edit(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        new_name = request.form.get("username")
        if new_name:
            user.name = new_name.title()
            db.session.commit()
            flash("User Updated successfully", "success")
            return redirect(url_for("show_users"))
    return render_template("edit.html", user=user)


@app.route("/delete/<int:user_id>")
def delete(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully", "success")
    return redirect(url_for("show_users"))


@app.route("/download")
def download_users():
    users = User.query.order_by(User.id).all()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Name"])

    for user in users:
        cw.writerow([user.id, user.name])

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={"content-Disposition": "attachment;filename=users.csv"},
    )


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
