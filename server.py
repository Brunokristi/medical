from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import datetime
import random
import platform
import subprocess
import os
import csv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
CORS(app)

def get_database_path():
    if os.name == "nt":  # Windows
        return os.path.join(os.environ["USERPROFILE"], "Documents", "ADOS")
    else:  # macOS/Linux
        return os.path.expanduser("~/Documents/ADOS")

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


@app.route("/save_patient", methods=["POST"])
def save_patient():
    database_path = get_database_path()
    file = "database.csv"
    database_path = os.path.join(database_path, file)

    # Ensure the ADOS directory exists
    os.makedirs(os.path.dirname(database_path), exist_ok=True)

    # Define CSV headers (Only the required fields)
    headers = [
        "Meno", "Rodné číslo", "Adresa", "Poistovňa", "Meno vypĺňajúceho",
        "ADOS", "Hlavný text", "Podtext 1", "Podtext 2", "Text koniec mesiaca", "Číslo dekurzu"
    ]

    # Create database if it does not exist
    if not os.path.exists(database_path):
        with open(database_path, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

    # Get patient data from the request
    data = request.json
    rodne_cislo = data.get("rodne_cislo", "").strip()

    if not rodne_cislo:
        return jsonify({"error": "Rodné číslo je povinné!"}), 400

    # Prepare new record with only required fields
    new_record = [
        data.get("meno", ""), data.get("rodne_cislo", ""), data.get("adresa", ""), data.get("poistovna", ""),
        data.get("name_worker", ""), data.get("company", ""), data.get("hl_text", ""), data.get("podtext_1", ""),
        data.get("podtext_2", ""), data.get("koniec_mesiaca", ""), data.get("entry_number", "")
    ]

    updated = False
    records = []

    # Read existing records
    with open(database_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        existing_records = list(reader)

    # Check if the Rodné číslo already exists and update the record
    for i, row in enumerate(existing_records):
        if row and row[1] == rodne_cislo:  # Match Rodné číslo
            existing_records[i] = new_record
            updated = True
            break

    # Append new record if no existing record found
    if not updated:
        existing_records.append(new_record)

    # Write back the updated records
    with open(database_path, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(existing_records)

    message = "Dáta boli úspešne aktualizované!" if updated else "Nový záznam bol pridaný!"
    return jsonify({"message": message})


def random_time(start, end):
    start_seconds = start.hour * 3600 + start.minute * 60
    end_seconds = end.hour * 3600 + end.minute * 60
    random_seconds = random.randint(start_seconds, end_seconds)
    return f"{random_seconds // 3600:02}:{(random_seconds % 3600) // 60:02}"

def open_pdf(pdf_path):
    if not os.path.isfile(pdf_path):
        print(f"PDF súbor neexistuje: {pdf_path}")
        return

    try:
        if platform.system() == "Windows":
            os.startfile(pdf_path)  # Opens file with default application
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", pdf_path], check=True)
        elif platform.system() == "Linux":
            subprocess.run(["xdg-open", pdf_path], check=True)
        else:
            print(f"Otvorte manuálne: {pdf_path}")  # Unknown OS
    except Exception as e:
        print(f"Chyba pri otváraní PDF: {e}")

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
        hl_text = data.get("hl_text")
        entry_number = data.get("entry_number")

        # Convert dates and times
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        start_time = datetime.datetime.strptime(start_time, "%H:%M").time()
        end_time = datetime.datetime.strptime(end_time, "%H:%M").time()
        write_start_time = datetime.datetime.strptime(write_start_time, "%H:%M").time()
        write_end_time = datetime.datetime.strptime(write_end_time, "%H:%M").time()

        # Generate schedule
        editable_schedule = []
        current_date = start_date

        while current_date <= end_date:
            weekday = current_date.weekday()

            if schedule_option == "Každý deň":
                editable_schedule.append([current_date.strftime('%d.%m.%Y'), start_time.strftime("%H:%M"), write_start_time.strftime("%H:%M"), hl_text])
            elif schedule_option == "Každý pracovný deň" and weekday < 5:
                editable_schedule.append([current_date.strftime('%d.%m.%Y'), start_time.strftime("%H:%M"), write_start_time.strftime("%H:%M"), hl_text])
            elif schedule_option == "3x v týždni" and weekday in [0, 2, 4]:
                editable_schedule.append([current_date.strftime('%d.%m.%Y'), start_time.strftime("%H:%M"), write_start_time.strftime("%H:%M"), hl_text])

            current_date += datetime.timedelta(days=1)

        if not editable_schedule:
            return jsonify({"error": "Neboli vygenerované žiadne dátumy."}), 400

        pdf_path = generate_pdf(editable_schedule, meno, rodne_cislo, adresa, poistovna, name_worker, company, entry_number)

        return jsonify({"message": "Plán bol úspešne vygenerovaný!", "pdf_url": f"/view_pdf?pdf_path={pdf_path}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_pdf(editable_schedule, meno, rodne_cislo, adresa, poistovna, name_worker, company, entry_number):
    if os.name == "nt":  # Windows
        documents_path =  os.path.join(os.environ["USERPROFILE"], "Documents", "ADOS")
    else:  # macOS/Linux
         documents_path = os.path.expanduser("~/Documents/ADOS")
    os.makedirs(documents_path, exist_ok=True)

    pdf_filename = f"{rodne_cislo}_{meno.replace(' ', '_')}.pdf"
    pdf_path = os.path.join(documents_path, pdf_filename)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    def draw_header():
        c.setFont("Helvetica-Bold", 14)
        c.drawString(180, height - 40, "DEKURZ OŠETROVATELSKEJ STAROSTLIVOSTI")
        c.setFont("Helvetica", 10)
        c.drawString(width - 200, height - 60, f"Číslo dekurzu: {entry_number}")

        # Company Info
        company_info = {
            "Andramed": ["Andramed, o.z.", "SNP 8, 98601 Fiľakovo", "ADOS"],
            "ADAMED": ["ADOS ADANED s. r. o.", "Jánošíkova 4989/2 979 01 Rimavská Sobota", "ADOS"]
        }
        company_details = company_info.get(company, ["", "", ""])

        c.drawString(55, height - 75, company_details[0])
        c.drawString(55, height - 90, company_details[1])
        c.drawString(55, height - 105, company_details[2])

        c.drawString(55, height - 120, "Meno pacienta:")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(55, height - 140, meno)
        c.setFont("Helvetica", 10)
        c.drawString(400, height - 120, "Rodné číslo:")
        c.drawString(400, height - 140, rodne_cislo)

        c.line(50, height - 150, width - 50, height - 150)

    draw_header()
    y_position = height - 170

    for date, zs_time, write_time, text in editable_schedule:
        if y_position < 100:
            c.showPage()
            draw_header()
            y_position = height - 170

        c.setFont("Helvetica", 10)
        c.drawString(55, y_position, f"{date} - {zs_time} (ZS), {write_time} (Zápis)")
        c.drawString(55, y_position - 15, text)
        y_position -= 30

    c.save()
    open_pdf(pdf_path)

@app.route("/view_pdf", methods=["GET"])
def view_pdf():
    """Flask route to open the generated PDF in the browser."""
    pdf_path = request.args.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({"error": "Súbor neexistuje"}), 404
    return send_file(pdf_path, mimetype="application/pdf")
if __name__ == "__main__":
    app.run(debug=True)
