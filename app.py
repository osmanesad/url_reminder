import sqlite3
from datetime import datetime, timedelta
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "url-reminder-local-dev"
DATABASE = "reminders.db"
PLACEHOLDER_IMAGE = "https://via.placeholder.com/320x180?text=No+Preview"
DEFAULT_SNOOZE_HOURS = 24


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def column_exists(conn, table_name, column_name):
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(column["name"] == column_name for column in columns)


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                description TEXT,
                image_url TEXT,
                source_domain TEXT,
                summary TEXT,
                category TEXT,
                tags TEXT,
                user_note TEXT,
                reminder_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

        legacy_columns = {
            "title": "ALTER TABLE reminders ADD COLUMN title TEXT",
            "description": "ALTER TABLE reminders ADD COLUMN description TEXT",
            "source_domain": "ALTER TABLE reminders ADD COLUMN source_domain TEXT",
            "summary": "ALTER TABLE reminders ADD COLUMN summary TEXT",
            "category": "ALTER TABLE reminders ADD COLUMN category TEXT",
            "tags": "ALTER TABLE reminders ADD COLUMN tags TEXT",
            "user_note": "ALTER TABLE reminders ADD COLUMN user_note TEXT",
            "status": "ALTER TABLE reminders ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'",
            "created_at": "ALTER TABLE reminders ADD COLUMN created_at TEXT",
            "updated_at": "ALTER TABLE reminders ADD COLUMN updated_at TEXT",
        }

        for column_name, sql in legacy_columns.items():
            if not column_exists(conn, "reminders", column_name):
                conn.execute(sql)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE reminders SET created_at = COALESCE(created_at, ?), updated_at = COALESCE(updated_at, ?)",
            (now, now),
        )
        conn.execute(
            "UPDATE reminders SET status = COALESCE(NULLIF(status, ''), 'pending')"
        )
        conn.commit()


def normalize_reminder_time(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def parse_reminder_time(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace(" ", "T"))


def format_reminder_time(value):
    if not value:
        return "-"
    parsed = parse_reminder_time(value)
    return parsed.strftime("%d.%m.%Y %H:%M")


def summarize_text(text, max_length=220):
    if not text:
        return ""
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3].rstrip() + "..."


def is_valid_url(value):
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def extract_metadata(url):
    metadata = {
        "title": url,
        "description": "",
        "image_url": PLACEHOLDER_IMAGE,
        "summary": "",
        "source_domain": urlparse(url).netloc.replace("www.", ""),
    }

    try:
        response = requests.get(
            url,
            timeout=8,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
                )
            },
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = (
            soup.find("meta", property="og:title")
            or soup.find("meta", attrs={"name": "twitter:title"})
        )
        description = (
            soup.find("meta", property="og:description")
            or soup.find("meta", attrs={"name": "description"})
            or soup.find("meta", attrs={"name": "twitter:description"})
        )
        image = (
            soup.find("meta", property="og:image")
            or soup.find("meta", attrs={"name": "twitter:image"})
        )

        page_title = title.get("content") if title and title.get("content") else None
        if not page_title and soup.title and soup.title.string:
            page_title = soup.title.string.strip()

        page_description = (
            description.get("content")
            if description and description.get("content")
            else ""
        )

        image_url = image.get("content") if image and image.get("content") else ""

        first_paragraph = ""
        paragraph = soup.find("p")
        if paragraph:
            first_paragraph = paragraph.get_text(" ", strip=True)

        metadata["title"] = page_title or metadata["title"]
        metadata["description"] = summarize_text(page_description, max_length=180)
        metadata["image_url"] = image_url or metadata["image_url"]

        summary_source = page_description or first_paragraph or metadata["title"]
        metadata["summary"] = summarize_text(summary_source)
    except Exception as exc:
        print("Metadata extraction failed:", exc)
        metadata["summary"] = "Onizleme alinamadi. Link kaydedildi, detaylar daha sonra duzenlenebilir."

    return metadata


def fetch_reminders():
    with get_connection() as conn:
        reminders = conn.execute(
            """
            SELECT id, url, title, description, image_url, source_domain, summary,
                   category, tags, user_note, reminder_time, status, created_at, updated_at
            FROM reminders
            ORDER BY datetime(reminder_time) ASC, id DESC
            """
        ).fetchall()

    now = datetime.now()
    sections = {
        "due": [],
        "upcoming": [],
        "done": [],
    }

    for row in reminders:
        item = dict(row)
        reminder_at = parse_reminder_time(item["reminder_time"])
        item["reminder_time_label"] = format_reminder_time(item["reminder_time"])
        item["is_overdue"] = item["status"] == "pending" and reminder_at <= now
        item["tags_list"] = [
            tag.strip() for tag in (item["tags"] or "").split(",") if tag.strip()
        ]

        if item["status"] in {"done", "archived"}:
            sections["done"].append(item)
        elif reminder_at <= now:
            sections["due"].append(item)
        else:
            sections["upcoming"].append(item)

    return sections


@app.route("/", methods=["GET"])
def index():
    sections = fetch_reminders()
    now_value = datetime.now().strftime("%Y-%m-%dT%H:%M")
    return render_template("index.html", sections=sections, now_value=now_value)


@app.route("/add", methods=["POST"])
def add():
    url_input = (request.form.get("url") or "").strip()
    category = (request.form.get("category") or "").strip()
    tags = (request.form.get("tags") or "").strip()
    user_note = (request.form.get("user_note") or "").strip()
    raw_reminder_time = request.form.get("reminder_time")

    if not url_input:
        flash("Link alani bos birakilamaz.", "error")
        return redirect(url_for("index"))

    if not is_valid_url(url_input):
        flash("Gecerli bir http veya https linki gir.", "error")
        return redirect(url_for("index"))

    try:
        reminder_time = normalize_reminder_time(raw_reminder_time)
    except ValueError:
        flash("Hatirlatma zamani gecersiz.", "error")
        return redirect(url_for("index"))

    if not reminder_time:
        flash("Hatirlatma zamani gerekli.", "error")
        return redirect(url_for("index"))

    metadata = extract_metadata(url_input)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO reminders (
                url, title, description, image_url, source_domain, summary,
                category, tags, user_note, reminder_time, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (
                url_input,
                metadata["title"],
                metadata["description"],
                metadata["image_url"],
                metadata["source_domain"],
                metadata["summary"],
                category,
                tags,
                user_note,
                reminder_time,
                now,
                now,
            ),
        )
        conn.commit()

    flash("Link kaydedildi.", "success")
    return redirect(url_for("index"))


@app.route("/reminders/<int:reminder_id>/action", methods=["POST"])
def update_status(reminder_id):
    action = request.form.get("action")
    now = datetime.now()
    updates = {"updated_at": now.strftime("%Y-%m-%d %H:%M:%S")}

    if action == "done":
        updates["status"] = "done"
    elif action == "archive":
        updates["status"] = "archived"
    elif action == "reopen":
        updates["status"] = "pending"
    elif action == "snooze":
        next_time = now + timedelta(hours=DEFAULT_SNOOZE_HOURS)
        updates["status"] = "pending"
        updates["reminder_time"] = next_time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        flash("Gecersiz islem.", "error")
        return redirect(url_for("index"))

    fields = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [reminder_id]

    with get_connection() as conn:
        conn.execute(f"UPDATE reminders SET {fields} WHERE id = ?", values)
        conn.commit()

    flash("Kayit guncellendi.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
