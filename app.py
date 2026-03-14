# from flask import Flask, render_template, request, redirect, session, send_file
# # from flask import Flask, render_template, redirect, session
# import sqlite3
# import json
# import io
# from reportlab.pdfgen import canvas

# app = Flask(__name__)
# app.secret_key = "secret123"

# def get_db():
#     return sqlite3.connect("users.db")

# def productivity_advice(total):

#     if total > 300:
#         return "⚠ High screen time detected. Consider taking breaks."
#     elif total > 200:
#         return "Moderate usage. Try reducing social media usage."
#     else:
#         return "Great! Your digital usage is balanced."

# @app.route("/")
# def dashboard():

#     if "user" not in session:
#         return redirect("/login")

#     try:
#         with open("usage.json") as f:
#             data = json.load(f)
#     except:
#         data = {}

#     apps = list(data.keys())
#     times = list(data.values())

#     total = sum(times)
#     advice = productivity_advice(total)

#     return render_template(
#         "index.html",
#         apps=apps,
#         times=times,
#         score=72,
#         advice=advice
#     )

# @app.route("/register", methods=["GET","POST"])
# def register():

#     if request.method == "POST":

#         username = request.form["username"]
#         password = request.form["password"]

#         db = get_db()
#         db.execute(
#             "INSERT INTO users(username,password) VALUES(?,?)",
#             (username,password)
#         )
#         db.commit()

#         return redirect("/login")

#     return render_template("register.html")

# @app.route("/login", methods=["GET","POST"])
# def login():

#     if request.method == "POST":

#         username = request.form["username"]
#         password = request.form["password"]

#         db = get_db()
#         user = db.execute(
#             "SELECT * FROM users WHERE username=? AND password=?",
#             (username,password)
#         ).fetchone()

#         if user:
#             session["user"] = username
#             return redirect("/")

#         return "Invalid Login"

#     return render_template("login.html")

# @app.route("/logout")
# def logout():
#     session.pop("user",None)
#     return redirect("/login")

# @app.route("/download")
# def download_report():

#     buffer = io.BytesIO()
#     p = canvas.Canvas(buffer)

#     p.drawString(100,800,"Digital Detox Report")

#     try:
#         with open("usage.json") as f:
#             data = json.load(f)
#     except:
#         data = {}

#     y = 760

#     for app,time in data.items():
#         p.drawString(100,y,f"{app} : {time} seconds")
#         y -= 20

#     p.save()
#     buffer.seek(0)

#     return send_file(
#         buffer,
#         as_attachment=True,
#         download_name="report.pdf"
#     )

# if __name__ == "__main__":
#     app.run(debug=True)


from reportlab.pdfgen import canvas
import io
from flask import send_file
from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import json

app = Flask(__name__)
app.secret_key = "secret123"


def get_db():
    return sqlite3.connect("users.db")


def productivity_advice(total):

    if total > 300:
        return "⚠ High screen time detected. Consider taking breaks."
    elif total > 200:
        return "Moderate usage. Try reducing social media usage."
    else:
        return "Great! Your digital usage is balanced."


@app.route("/")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    try:
        with open("usage.json") as f:
            data = json.load(f)
    except:
        data = {}

    apps = list(data.keys())
    times = list(data.values())

    total = sum(times)
    score = max(0, 100 - total // 10)

    advice = productivity_advice(total)

    return render_template(
        "index.html",
        apps=apps,
        times=times,
        score=score,
        advice=advice
    )


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        db.execute(
            "INSERT INTO users (username,password) VALUES (?,?)",
            (username, password)
        )
        db.commit()

        flash("Registration successful! Please login.")
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        if user:
            session["user"] = username
            flash("Welcome to Digital Detox Tracker!")
            return redirect("/")

        flash("Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.pop("user", None)
    return redirect("/login")


# DOWNLOAD REPORT ROUTE
@app.route("/download")
def download_report():

    if "user" not in session:
        return redirect("/login")

    try:
        with open("usage.json") as f:
            data = json.load(f)
    except:
        data = {}

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(300, 800, "Digital Detox Report")

    pdf.setFont("Helvetica", 12)

    y = 750

    for app, time in data.items():

        # shorten very long titles
        if len(app) > 40:
            app = app[:40] + "..."

        text = f"{app} : {time} seconds"

        pdf.drawString(80, y, text)

        y -= 25

        if y < 100:   # new page if needed
            pdf.showPage()
            y = 750

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="digital_detox_report.pdf",
        mimetype="application/pdf"
    )
if __name__ == "__main__":
    app.run(debug=True)