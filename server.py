from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, flash
from flask_cors import CORS
import datetime
import random
import re
import os
import csv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import platform
import subprocess
import webbrowser
import threading
import os
import sys
import sqlite3
from datetime import datetime, timedelta
import calendar



app = Flask(__name__)
CORS(app)

DATABASE_FILE = "ados_database.db"
app.secret_key = "a3f8d3e87b5a4e5f9c6d4b2f6a1e8c3d"


def get_database_path():
    if os.name == "nt":  # Windows
        return os.path.join(os.environ["USERPROFILE"], "Documents", "ADOS")
    else:  # macOS/Linux
        return os.path.expanduser("~/Documents/ADOS")

def random_time(start, end):
    start_seconds = start.hour * 3600 + start.minute * 60
    end_seconds = end.hour * 3600 + end.minute * 60
    random_seconds = random.randint(start_seconds, end_seconds)
    return f"{random_seconds // 3600:02}:{(random_seconds % 3600) // 60:02}"

def replace_slovak_chars(text):
    """Replaces Slovak characters that might not render correctly in the PDF."""
    replacements = {
        "č": "c", "ť": "t", "ž": "z", "ý": "y", "ú": "u", "ľ": "l",
        "ď": "d", "ň": "n", "ó": "o", "ř": "r", "ě": "e"
    }
    return "".join(replacements.get(char, char) for char in text)

    database_path = get_database_path()
    file = "database.csv"
    database_path = os.path.join(database_path, file)

    os.makedirs(os.path.dirname(database_path), exist_ok=True)

    headers = [
        "Meno", "Rodné číslo", "Adresa", "Poistovňa", "Meno vypĺňajúceho",
        "ADOS", "Hlavný text", "Podtext 1", "Podtext 2", "Text koniec mesiaca", "Číslo dekurzu"
    ]

    if not os.path.exists(database_path):
        with open(database_path, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

    if not rodne_cislo:
        return jsonify({"error": "Rodné číslo je povinné!"}), 400

    new_record = [
        meno, rodne_cislo, adresa, poistovna, name_worker, company, hl_text, podtext_1, podtext_2, koniec_mesiaca, entry_number
    ]

    updated = False
    records = []

    with open(database_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        existing_records = list(reader)

    for i, row in enumerate(existing_records):
        if row and row[1] == rodne_cislo:
            existing_records[i] = new_record
            updated = True
            break

    if not updated:
        existing_records.append(new_record)

    with open(database_path, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(existing_records)

    message = "Dáta boli úspešne aktualizované!" if updated else "Nový záznam bol pridaný!"
    return jsonify({"message": message})

def generate_pdf(editable_schedule, meno, rodne_cislo, adresa, poistovna, name_worker, company, entry_number, hl_text, podtext_1, podtext_2, koniec_mesiaca):
    if os.name == "nt":  # Windows
        documents_path = os.path.join(os.environ["USERPROFILE"], "Documents", "ADOS")
    else:  # macOS/Linux
        documents_path = os.path.expanduser("~/Documents/ADOS")

    os.makedirs(documents_path, exist_ok=True)

    sanitized_rc = re.sub(r'[^0-9]', '', rodne_cislo)
    document_date = datetime.datetime.strptime(editable_schedule[0][0], "%d.%m.%Y").strftime("%m%Y")
    sanitized_name = meno.replace(" ", "_")

    pdf_filename = f"{sanitized_rc}_{document_date}_{sanitized_name}.pdf"
    pdf_path = os.path.join(documents_path, pdf_filename)
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    page_number = int(entry_number)

    def draw_header():
        c.setFont("Helvetica-Bold", 14)
        
        title_text = replace_slovak_chars("DEKURZ OŠETROVATELSKEJ STAROSTLIVOSTI")
        title_width = c.stringWidth(title_text, "Helvetica-Bold", 14)
        c.drawString((width - title_width) / 2, height - 40, title_text)

        c.setFont("Helvetica", 10)
        c.drawString(width - 200, height - 60, f"Poradové císlo strany dekurzu: {page_number}")

        # Draw company information box
        c.setStrokeColor(colors.black)
        c.rect(50, height - 110, width - 100, 45, stroke=1, fill=0)

        company_info = {
            "Andramed": ["Andramed, o.z.", "SNP 8, 98601 Fiľakovo", "ADOS"],
            "ADAMED": ["ADOS ADANED s. r. o.", "Jánošíkova 4989/2 979 01 Rimavská Sobota", "ADOS"]
        }
        company_details = company_info.get(company, ["", "", ""])

        c.setFont("Helvetica", 10)
        c.drawString(55, height - 75, replace_slovak_chars(company_details[0]))
        c.drawString(55, height - 90, replace_slovak_chars(company_details[1]))
        c.drawString(55, height - 105, replace_slovak_chars(company_details[2]))

        # Patient details
        c.drawString(55, height - 120, replace_slovak_chars("Meno, priezvisko, titul pacienta/pacientky:"))
        c.drawString(400, height - 120, replace_slovak_chars("Rodné číslo:"))

        c.setFont("Helvetica-Bold", 12)
        c.drawString(55, height - 140, meno)
        c.drawString(400, height - 140, rodne_cislo)

        # Draw separation lines
        c.rect(50, height - 150, width - 100, 40, stroke=1, fill=0)
        c.line(395, height - 150, 395, height - 110)
        c.rect(50, height - 185, width - 100, 35, stroke=1, fill=0)

        # Draw table headers
        c.setFont("Helvetica", 10)
        c.drawString(55, height - 170, replace_slovak_chars("Dátum a"))
        c.drawString(55, height - 182, replace_slovak_chars("čas zápisu:"))

        c.line(145, height - 185, 145, height - 150)

        c.drawString(150, height - 170, replace_slovak_chars("Rozsah poskytnutej ZS a služieb súvisiacich s poskytnutím ZS, identifikácia ošetrujúceho"))
        c.drawString(150, height - 180, replace_slovak_chars("zdravotného pracovníka (meno, priezvisko, odtlačok pečiatky a podpis)"))

        c.rect(50, height - 800, width - 100, 615, stroke=1, fill=0)
        c.line(145, height - 800, 145, height - 185)

    draw_header()
    c.setFont("Helvetica", 10)
    y_position = height - 200  

    for date, zs_time, write_time, text in editable_schedule:
        text = zs_time + ": " + text
        c.setFont("Helvetica", 10)
        c.drawString(55, y_position, date)
        c.drawString(55, y_position - 10, write_time)

        text_lines = text.split("\n")  # Handle multi-line text manually
        for line in text_lines:
            c.drawString(150, y_position, replace_slovak_chars(line))
            y_position -= 15

        # Nurse's Signature
        c.setFont("Helvetica-Bold", 10)
        c.drawString(150, y_position, name_worker)
        c.setFont("Helvetica", 10)
        c.drawString(300, y_position, "Podpis:")
        y_position -= 15

        y_position -= 20

        # Ensure new page if needed
        if y_position < 100:
            c.showPage()
            page_number += 1
            draw_header()
            y_position = height - 200

    c.save()
    save_patient(meno, rodne_cislo, adresa, poistovna, name_worker, company, str(page_number+1), hl_text, podtext_1, podtext_2, koniec_mesiaca)
    open_pdf(pdf_path)

    return pdf_path

def open_pdf(pdf_path):
    if os.name == "nt":
        os.system(f'start "" "{pdf_path}"')
    else:
        os.system(f"open '{pdf_path}'")

@app.route('/open-folder', methods=['GET'])
def open_folder():
    folder_path = os.path.expanduser("~/Documents/ados")  # Adjust for Windows if needed

    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", folder_path])
        elif platform.system() == "Windows":  # Windows
            subprocess.run(["explorer", folder_path])
        
        return jsonify({"status": "success", "message": "Folder opened successfully"})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    

@app.route("/generate_schedule", methods=["POST"])
def generate_schedule():
    try:
        data = request.json

        # Extract form data
        meno = data.get("meno")
        rodne_cislo = data.get("rodne_cislo")
        adresa = data.get("adresa")
        poistovna = data.get("poistovna")
        start_date = data.get("date_start")
        end_date = data.get("date_end")
        start_time = data.get("zs_start_time")
        end_time = data.get("zs_end_time")
        write_start_time = data.get("write_start_time")
        write_end_time = data.get("write_end_time")
        schedule_option = data.get("schedule")
        name_worker = data.get("name_worker")
        company = data.get("company")
        hl_text = data.get("hl_text")  # Main text
        entry_number = data.get("entry_number")

        # Additional texts and their corresponding dates
        podtext_1 = data.get("podtext_1")
        dates_podtext_1 = data.get("dates_podtext_1").split(",") if data.get("dates_podtext_1") else []
        podtext_2 = data.get("podtext_2")
        dates_podtext_2 = data.get("dates_podtext_2").split(",") if data.get("dates_podtext_2") else []
        koniec_mesiaca = data.get("koniec_mesiaca")
        dates_koniec_mesiaca = data.get("dates_koniec_mesiaca").split(",") if data.get("dates_koniec_mesiaca") else []

        # Convert dates and times
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        start_time = datetime.datetime.strptime(start_time, "%H:%M").time()
        end_time = datetime.datetime.strptime(end_time, "%H:%M").time()
        write_start_time = datetime.datetime.strptime(write_start_time, "%H:%M").time()
        write_end_time = datetime.datetime.strptime(write_end_time, "%H:%M").time()

        # Dictionary to store texts by date (handles multiple texts per date)
        text_by_date = {}

        def add_text_to_date(date_str, text, category):
            formatted_date = datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d").strftime('%d.%m.%Y')
            if formatted_date not in text_by_date:
                text_by_date[formatted_date] = {"podtext_2": [], "podtext_1": [], "hl_text": [], "koniec_mesiaca": []}
            
            text_by_date[formatted_date][category].append(text)

        # Store all texts in dictionary with explicit order
        for date in dates_podtext_2:
            add_text_to_date(date, podtext_2, "podtext_2")  # 🔹 First (Highest Priority)

        for date in dates_podtext_1:
            add_text_to_date(date, podtext_1, "podtext_1")  # 🔹 Before hlavný text

        for date in dates_koniec_mesiaca:
            add_text_to_date(date, koniec_mesiaca, "koniec_mesiaca")  # 🔹 Last (Final Summary)

        # Generate schedule
        editable_schedule = []
        current_date = start_date

        while current_date <= end_date:
            formatted_date = current_date.strftime('%d.%m.%Y')
            weekday = current_date.weekday()

            if schedule_option == "Každý deň" or (schedule_option == "Každý pracovný deň" and weekday < 5) or (schedule_option == "3x v týždni" and weekday in [0, 2, 4]):
                combined_texts = []  

                if formatted_date in text_by_date:

                    combined_texts.extend(text_by_date[formatted_date]["podtext_2"])
                    combined_texts.extend(text_by_date[formatted_date]["podtext_1"])

                combined_texts.append(hl_text)

                if formatted_date in text_by_date and text_by_date[formatted_date]["koniec_mesiaca"]:
                    combined_texts.extend(text_by_date[formatted_date]["koniec_mesiaca"])

                editable_schedule.append([
                    formatted_date,
                    random_time(start_time, end_time),
                    random_time(write_start_time, write_end_time),
                    "\n\n".join(combined_texts)
                ])

            current_date += datetime.timedelta(days=1)

        if not editable_schedule:
            return jsonify({"error": "Neboli vygenerované žiadne dátumy."}), 400

        # Generate PDF
        pdf_path = generate_pdf(editable_schedule, meno, rodne_cislo, adresa, poistovna, name_worker, company, entry_number, hl_text, podtext_1, podtext_2, koniec_mesiaca)

        return jsonify({"message": "Plán bol úspešne vygenerovaný!", "pdf_path": pdf_path})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/")
def index():
    conn = get_db_connection()
    nurses = conn.execute("SELECT * FROM sestry").fetchall()
    conn.close()
    return render_template("login.html", nurses=nurses)

@app.route("/add_nurse", methods=["POST"])
def add_nurse():
    name = request.form.get("meno").strip()

    if not name:
        flash("Nurse name cannot be empty!", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO sestry (meno) VALUES (?)", (name,))
        conn.commit()
        flash(f"Nurse '{name}' added successfully!", "success")
    except sqlite3.Error as e:
        flash(f"Database error: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for("index"))




def generate_dates(cursor, month_id, year, month):
    days_in_month = calendar.monthrange(year, month)[1]

    # Insert each day into the dni table
    for day in range(1, days_in_month + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"  # Format YYYY-MM-DD
        cursor.execute("INSERT INTO dni (datum, mesiac) VALUES (?, ?)", (date_str, month_id))

@app.route("/month", methods=["POST"])
def month():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get JSON data from fetch request
        data = request.get_json()

        nurse_id = data.get("nurse")
        month_input = data.get("month")
        zs_start_time = data.get("zs_start_time")
        zs_end_time = data.get("zs_end_time")
        write_start_time = data.get("write_start_time")
        write_end_time = data.get("write_end_time")

        if not month_input or not nurse_id:
            return jsonify({"error": "Mesiac a sestra sú povinné!"}), 400

        # Extract year and month from YYYY-MM format
        year, month = map(int, month_input.split("-"))

        # Check if the month already exists
        cursor.execute("SELECT id FROM mesiac WHERE mesiac = ? AND rok = ? AND sestra_id = ?", (month, year, nurse_id))
        existing_month = cursor.fetchone()

        if existing_month:
            flash("Mesiac už existuje, načítavam dáta...", "info")
            conn.close()
            return jsonify({"redirect": url_for("detail", nurse_id=nurse_id, year=year, month=month)})

        # Insert new month if it does not exist
        cursor.execute("""
            INSERT INTO mesiac (mesiac, rok, vysetrenie_start, vysetrenie_koniec, vypis_start, vypis_koniec, sestra_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (month, year, zs_start_time, zs_end_time, write_start_time, write_end_time, nurse_id))
        conn.commit()

        # Retrieve the newly inserted month ID
        cursor.execute("SELECT id FROM mesiac WHERE mesiac = ? AND rok = ? AND sestra_id = ? ", (month, year, nurse_id))
        month_id = cursor.fetchone()["id"]

        # Generate and insert all days of the month
        generate_dates(cursor, month_id, year, month)
        conn.commit()  # Ensure days are committed to the database

        flash("Mesiac a jeho dátumy boli úspešne vytvorené!", "success")

        conn.close()

        # Redirect to the detail page for that month
        return jsonify({"redirect": url_for("detail", nurse_id=nurse_id, year=year, month=month)})

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500



@app.route("/save_patient", methods=["POST"])
def save_patient():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get JSON data from request
        data = request.get_json()

        # Use .get() with a default empty string if value is missing
        meno = data.get("meno", "").strip()
        rodne_cislo = data.get("rodne_cislo", "").strip()
        adresa = data.get("adresa", "").strip()
        poistovna = data.get("poistovna", "").strip()
        ados = data.get("ados", "").strip()
        sestra = data.get("sestra", "").strip()
        nalez = data.get("nalez", "").strip()
        osetrenie = data.get("osetrenie", "").strip()
        vedlajsie_osetrenie = data.get("vedlajsie_osetrenie", "").strip()
        koniec_mesiaca = data.get("koniec_mesiaca", "").strip()
        cislo_dekurzu = data.get("cislo_dekurzu", "").strip()
        vypisane = data.get("vypisane", False)  # Keep False as default for booleans

        if not meno or not rodne_cislo:
            return jsonify({"error": "Meno a rodné číslo sú povinné!"}), 400

        # Check if the patient already exists
        cursor.execute("SELECT id FROM pacienti WHERE rodne_cislo = ?", (rodne_cislo,))
        existing_patient = cursor.fetchone()

        if existing_patient:
            # Patient exists, update the record
            patient_id = existing_patient["id"]
            cursor.execute("""
                UPDATE pacienti
                SET meno = ?, adresa = ?, poistovna = ?, ados = ?, sestra = ?, nalez = ?, osetrenie = ?, 
                    vedlajsie_osetrenie = ?, koniec_mesiaca = ?, cislo_dekurzu = ?, vypisane = ?
                WHERE id = ?
            """, (meno, adresa, poistovna, ados, sestra, nalez, osetrenie, vedlajsie_osetrenie, koniec_mesiaca, cislo_dekurzu, vypisane, patient_id))
            message = "Pacient bol úspešne aktualizovaný!"
        else:
            # Insert new patient
            cursor.execute("""
                INSERT INTO pacienti (meno, rodne_cislo, adresa, poistovna, ados, sestra, nalez, osetrenie, vedlajsie_osetrenie, koniec_mesiaca, cislo_dekurzu, vypisane)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (meno, rodne_cislo, adresa, poistovna, ados, sestra, nalez, osetrenie, vedlajsie_osetrenie, koniec_mesiaca, cislo_dekurzu, vypisane))
            message = "Pacient bol úspešne pridaný!"

        conn.commit()
        conn.close()

        return jsonify({"message": message}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/search_patient", methods=["GET"])
def search_patient():    
    query = request.args.get("query", "").strip()
    
    if len(query) < 3:
        return jsonify([])

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, meno, rodne_cislo, adresa, poistovna, sestra, ados, nalez, osetrenie, vedlajsie_osetrenie, koniec_mesiaca, cislo_dekurzu
            FROM pacienti
            WHERE meno LIKE ? OR rodne_cislo LIKE ?
        """, (f"%{query}%", f"%{query}%"))

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["id"],
                "rc": row["rodne_cislo"],  # Rodné číslo
                "name": row["meno"],  # Meno
                "address": row["adresa"],  # Adresa
                "insurance": row["poistovna"],  # Poistovňa
                "worker": row["sestra"],  # ID sestry (can be used to fetch name)
                "company": row["ados"],  # ADOS
                "hl_text": row["nalez"],  # Hlavný text
                "podtext_1": row["osetrenie"],  # Podtext 1
                "podtext_2": row["vedlajsie_osetrenie"],  # Podtext 2
                "koniec_mesiaca": row["koniec_mesiaca"],  # Text koniec mesiaca
                "entry_number": row["cislo_dekurzu"]  # Číslo dekurzu
            })

        conn.close()
        return jsonify(results)

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500




@app.route("/detail/<int:nurse_id>/", defaults={"year": None, "month": None, "day": None}, methods=["GET", "POST"])
@app.route("/detail/<int:nurse_id>/<int:year>/", defaults={"month": None, "day": None}, methods=["GET", "POST"])
@app.route("/detail/<int:nurse_id>/<int:year>/<int:month>/", defaults={"day": None}, methods=["GET", "POST"])
@app.route("/detail/<int:nurse_id>/<int:year>/<int:month>/<int:day>/", methods=["GET", "POST"])
def detail(nurse_id, year, month, day):
    try:
        conn = get_db_connection()
        cursor = conn.cursor() 

        # nurse
        cursor.execute("SELECT * FROM sestry WHERE id = ?", (nurse_id,))
        nurse = cursor.fetchone()

        if not nurse:
            conn.close()
            flash("Nurse not found!", "danger")
            return redirect(url_for("index"))
        
        
        month_data = None
        days = []
        patients_in_month = []
        patients_in_day = []

        if year and month:
            cursor.execute("SELECT * FROM mesiac WHERE mesiac = ? AND rok = ?", (month, year))
            month_data = cursor.fetchone()

            if month_data:
                cursor.execute("SELECT * FROM dni WHERE mesiac = ?", (month_data["id"],))
                days = cursor.fetchall()

                cursor.execute("""
                    SELECT DISTINCT pacienti.* FROM pacienti
                    JOIN den_pacient ON pacienti.id = den_pacient.pacient_id
                    JOIN dni ON den_pacient.den_id = dni.id
                    WHERE dni.mesiac = ?
                """, (month_data["id"],))
                patients_in_month = cursor.fetchall()

        if day:
            cursor.execute("""
                SELECT pacienti.* FROM pacienti
                JOIN den_pacient ON pacienti.id = den_pacient.pacient_id
                WHERE den_pacient.den_id = ?
            """, (day,))
            patients_in_day = cursor.fetchall()

        conn.close()

        return render_template("index.html", 
                               nurse=nurse, 
                               month=month_data, 
                               days=days, 
                               patients_in_month=patients_in_month, 
                               patients_in_day=patients_in_day)

    except Exception as e:
        flash(f"Chyba: {e}", "danger")
        return redirect(url_for("detail"))



def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def check_db():
    if not os.path.exists(DATABASE_FILE):
        initialize_db()

def initialize_db():
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE sestry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meno TEXT NOT NULL
            );

            CREATE TABLE mesiac (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mesiac INTEGER NOT NULL,
                rok INTEGER NOT NULL,
                vysetrenie_start TIME NOT NULL,
                vysetrenie_koniec TIME NOT NULL,
                vypis_start TIME NOT NULL,
                vypis_koniec TIME NOT NULL,
                sestra_id INTEGER NOT NULL,
                FOREIGN KEY (sestra_id) REFERENCES sestry(id) ON DELETE CASCADE
            );

            CREATE TABLE dni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mesiac INTEGER NOT NULL,
                datum DATE NOT NULL,
                FOREIGN KEY (mesiac) REFERENCES mesiac(id) ON DELETE CASCADE
            );

            CREATE TABLE pacienti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meno TEXT NOT NULL,
                rodne_cislo UNIQUE NOT NULL,
                adresa TEXT NOT NULL,
                poistovna TEXT NOT NULL,
                ados TEXT NOT NULL,
                sestra INTEGER NOT NULL,
                nalez TEXT,
                osetrenie TEXT,
                vedlajsie_osetrenie TEXT,
                koniec_mesiaca TEXT,
                cislo_dekurzu INTEGER,
                vypisane BOOLEAN DEFAULT 0,
                FOREIGN KEY (sestra) REFERENCES sestry(id) ON DELETE SET NULL
            );

            CREATE TABLE den_pacient (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                den_id INTEGER NOT NULL,
                pacient_id INTEGER NOT NULL,
                vysetrenie DATETIME NOT NULL,
                vypis DATETIME,
                poradie_pacienta INTEGER,
                FOREIGN KEY (den_id) REFERENCES dni(id) ON DELETE CASCADE,
                FOREIGN KEY (pacient_id) REFERENCES pacienti(id) ON DELETE CASCADE
            );
        """)

if __name__ == "__main__":
    check_db()
    threading.Timer(1.5, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)