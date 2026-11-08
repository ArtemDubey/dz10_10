from flask import Flask, jsonify, template_rendered, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.json.ensure_ascii = False


def get_db_connection():
    conn = sqlite3.connect("tours.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        '''
            CREATE TABLE IF NOT EXISTS tours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image TEXT NOT NULL,
                season TEXT DEFAULT 'Універсальний'
            )
        '''
    )

    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(tours)")
    columns = [column[1] for column in cursor.fetchall()]
    if "season" not in columns:
        conn.execute("ALTER TABLE tours ADD COLUMN season TEXT DEFAULT 'Універсальний'")

    conn.commit()
    conn.close()


init_db()


def calculate_seasonal_price(base_price, tour_season):
    current_month = datetime.now().month

    if current_month in [12, 1, 2]:
        current_season = "Зима"
    elif current_month in [3, 4, 5]:
        current_season = "Весна"
    elif current_month in [6, 7, 8]:
        current_season = "Літо"
    else:
        current_season = "Осінь"
    if tour_season == current_season:
        final_price = round(base_price * 0.85, 2)
        diff = round(final_price - base_price, 2)
        text = f"Сезонна знижка: {diff} $"
    elif tour_season != "Універсальний" and tour_season:
        final_price = round(base_price * 1.1, 2)
        diff = round(final_price - base_price, 2)
        text = f"Сезонна надбавка: +{diff} $"
    else:
        final_price = base_price
        text = "Стандартна ціна"

    return final_price, text


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/tours")
def tours():
    conn = get_db_connection()
    raw_tours = conn.execute("SELECT * FROM tours").fetchall()
    conn.close()

    tours_list = []
    for tour in raw_tours:
        final_price, price_info = calculate_seasonal_price(tour['price'], tour['season'])

        tours_list.append({
            'id': tour['id'],
            'title': tour['title'],
            'description': tour['description'],
            'base_price': tour['price'],
            'final_price': final_price,
            'image': tour['image'],
            'season': tour['season'],
            'price_info': price_info
        })

    return render_template("tours.html", tours=tours_list)


@app.route("/add_tour", methods=["GET", "POST"])
def add_tour():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        price_str = request.form.get("price", "").strip()
        image = request.form.get("image", "").strip()
        season = request.form.get("season", "Універсальний").strip()

        if title and image:
            try:
                price = float(price_str)
                if price >= 0:
                    conn = get_db_connection()
                    conn.execute(
                        "INSERT INTO tours (title, description, price, image, season) VALUES (?, ?, ?, ?, ?)",
                        (title, description, price, image, season),
                    )
                    conn.commit()
                    conn.close()
                    return redirect(url_for("tours"))
            except ValueError:
                pass

    return render_template("add_tour.html")


@app.route("/gallery")
def gallery():
    return render_template("gallery.html")


@app.route("/contacts")
def contacts():
    return render_template("contacts.html")


@app.route("/edit_tour/<int:id>", methods=["GET", "POST"])
def edit_tour(id):
    conn = get_db_connection()
    tour = conn.execute("SELECT * FROM tours WHERE id = ?", (id,)).fetchone()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        price_str = request.form.get("price", "").strip()
        image = request.form.get("image", "").strip()
        season = request.form.get("season", "Універсальний").strip()

        if title and image:
            try:
                price = float(price_str)
                if price >= 0:
                    conn.execute(
                        '''
                        UPDATE tours 
                        SET title = ?, description = ?, price = ?, image = ?, season = ?
                        WHERE id = ?
                    ''',
                        (title, description, price, image, season, id),
                    )
                    conn.commit()
                    conn.close()
                    return redirect(url_for("tours"))
            except ValueError:
                pass

    conn.close()
    return render_template("edit_tour.html", tour=tour)


@app.route("/delete_tour/<int:id>", methods=["POST"])
def delete_tour(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM tours WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("tours"))


@app.route('/pick', methods=['GET', 'POST'])
def pick_tour():
    tours = None
    people_count = 1
    if request.method == 'POST':
        try:
            budget = float(request.form['budget'])
            people_count = int(request.form['people'])
        except ValueError:
            budget = 0
            people_count = 1

        conn = get_db_connection()
        tours = conn.execute("SELECT * FROM tours").fetchall()
        conn.close()

        tours = [tour for tour in tours if (tour['price'] * people_count) <= budget]
        tours = sorted(tours, key=lambda x: x['price'])

    return render_template('pick.html', tours=tours, people_count=people_count)


if __name__ == '__main__':
    app.run(debug=True)