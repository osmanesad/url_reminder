from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)
DATABASE = "reminders.db"


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS reminders (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            url TEXT NOT NULL,
                            image_url TEXT,
                            reminder_time TEXT
                        )"""
        )
        conn.commit()


def get_preview_image(url):
    """
    Web adresinin HTML'ini çekip, varsa og:image meta etiketini bulur.
    Eğer bulunamazsa varsayılan bir placeholder görsel URL'si döner.
    """
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            return meta.get("content")
    except Exception as e:
        print("Preview görüntüsü alınırken hata:", e)
    return "https://via.placeholder.com/150"


@app.route("/", methods=["GET"])
def index():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, url, image_url, reminder_time FROM reminders")
        reminders = cur.fetchall()
    return render_template("index.html", reminders=reminders)


@app.route("/add", methods=["POST"])
def add():
    url_input = request.form.get("url")
    reminder_time = request.form.get("reminder_time")  # datetime-local formatında gelir
    if url_input:
        image_url = get_preview_image(url_input)
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO reminders (url, image_url, reminder_time) VALUES (?, ?, ?)",
                (url_input, image_url, reminder_time),
            )
            conn.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
