from flask import Flask, request, jsonify, send_file, render_template
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

app = Flask(__name__)
CORS(app)

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

def save_patient(meno, rodne_cislo, adresa, poistovna, name_worker, company, entry_number, hl_text, podtext_1, podtext_2, koniec_mesiaca):
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
    
@app.route("/search_patient", methods=["GET"])
def search_patient():    
    query = request.args.get("query", "").strip()
    if len(query) < 3:
        return jsonify([])

    database_path = get_database_path()
    file = "database.csv"
    database_path = os.path.join(database_path, file)
    if not os.path.isfile(database_path):
        return jsonify({"error": "Databáza neexistuje"}), 404

    results = []
    with open(database_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader, None)  # Read header row

        for row in reader:
            if len(row) >= 11 and row[1].startswith(query):  # Ensure valid row and match Rodné číslo
                results.append({
                    "rc": row[1],  # Rodné číslo
                    "name": row[0],  # Meno
                    "address": row[2],  # Adresa
                    "insurance": row[3],  # Poistovňa
                    "worker": row[4],  # Meno vypĺňajúceho
                    "company": row[5],  # ADOS
                    "hl_text": row[6],  # Hlavný text
                    "podtext_1": row[7],  # Podtext 1
                    "podtext_2": row[8],  # Podtext 2
                    "koniec_mesiaca": row[9],  # Text koniec mesiaca
                    "entry_number": row[10]  # Číslo dekurzu
                })

    return jsonify(results)

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

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/route')
def route():
    return render_template('route.html')

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()  # Delay to ensure the server starts first
    app.run(host="127.0.0.1", port=5000, debug=False)