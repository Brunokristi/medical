import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit
import random
import datetime
import os
import platform
import re
import csv


editable_schedule = []
today = datetime.date.today().strftime("%d/%m/%Y")


def date_change(entry_widget, entry_var):
    text = entry_var.get().replace("/", "")
    
    if len(text) > 8:
        text = text[:8]

    formatted = ""
    cursor_position = entry_widget.index(tk.INSERT)
    count_slash = 0

    for i, char in enumerate(text):
        if i == 2 or i == 4:
            formatted += "/"
            count_slash += 1
        formatted += char

    entry_var.set(formatted)

    new_position = cursor_position + count_slash
    if new_position > len(formatted):
        new_position = len(formatted)

    entry_widget.icursor(new_position)

def rc_change(entry_widget, entry_var):
    
    text = entry_var.get().replace("/", "")
    cursor_position = entry_widget.index(tk.INSERT)
    
    if len(text) > 10:
        text = text[:10]

    formatted = ""
    slash_inserted = False

    for i, char in enumerate(text):
        if i == 6:
            formatted += "/"
            slash_inserted = True
        formatted += char

    entry_var.set(formatted)

    new_position = cursor_position
    if slash_inserted and cursor_position > 6:
        new_position += 1
    elif text == "":
        new_position = 0
    elif cursor_position > len(formatted):
        new_position = len(formatted)

    entry_widget.icursor(new_position)

def time_change(entry_widget, entry_var):
    text = entry_var.get().replace(":", "")
    cursor_position = entry_widget.index(tk.INSERT)

    if len(text) > 4:
        text = text[:4]

    formatted = ""
    colon_inserted = False

    for i, char in enumerate(text):
        if i == 2:
            formatted += ":"
            colon_inserted = True
        formatted += char

    entry_var.set(formatted)

    new_position = cursor_position
    if colon_inserted and cursor_position > 2: 
        new_position += 1
    elif text == "": 
        new_position = 0
    elif cursor_position > len(formatted): 
        new_position = len(formatted)

    entry_widget.icursor(new_position)

def save_patient_data():
    meno = entry_meno.get().strip()
    rodne_cislo = entry_rc.get().strip()
    adresa = entry_adresa.get().strip()
    poistovna = entry_poistovna.get().strip()

    if platform.system() == "Windows":
        documents_path = os.path.join(os.environ["USERPROFILE"], "Documents", "ADOS")  # Windows path
    else:
        documents_path = os.path.expanduser("~/Documents/ADOS")
    
    os.makedirs(documents_path, exist_ok=True)
    csv_file = os.path.join(documents_path, "pacienti_databaza.csv")

    patients = []
    file_exists = os.path.isfile(csv_file)
    updated = False

    if file_exists:
        with open(csv_file, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            header = next(reader, None)  # Read header
            for row in reader:
                if len(row) >= 2:  # Ensure valid row
                    if row[1] == rodne_cislo:  # If Rodné číslo matches, update data
                        row[0] = meno
                        row[2] = adresa
                        row[3] = poistovna
                        updated = True
                    patients.append(row)

    # If patient not found, add new entry
    if not updated:
        patients.append([meno, rodne_cislo, adresa, poistovna])

    # Write updated data back to CSV
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Meno", "Rodné číslo", "Adresa", "Zdravotná poisťovňa"])  # Write header
        writer.writerows(patients)

def save_entry_data():
    rodne_cislo = entry_rc.get().strip()
    start_date_str = date_start.get_date().strftime("%d/%m/%Y")
    extra_text = text_extra.get("1.0", "end-1c").strip()

    if not rodne_cislo or not start_date_str or not extra_text:
        messagebox.showwarning("Chyba", "Vyplňte všetky povinné polia.")
        return

    # Extract Month & Year from start_date
    try:
        start_date = datetime.datetime.strptime(start_date_str, "%d/%m/%Y")
        month_year = start_date.strftime("%m/%Y")  # Format as MM/YYYY
    except ValueError:
        messagebox.showwarning("Chyba", "Neplatný formát dátumu.")
        return

    # Define path to CSV file
    if platform.system() == "Windows":
        documents_path = os.path.join(os.environ["USERPROFILE"], "Documents", "ADOS")  # Windows path
    else:
        documents_path = os.path.expanduser("~/Documents/ADOS")  # macOS/Linux path
    
    os.makedirs(documents_path, exist_ok=True)  # Ensure folder exists
    csv_file = os.path.join(documents_path, "nalezy_databaza.csv")

    # Check if the file exists to add a header
    file_exists = os.path.isfile(csv_file)

    # Write to CSV
    with open(csv_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Rodné číslo", "Dátum (Mesiac/Rok)", "Nález"])  # Header row
        writer.writerow([rodne_cislo, month_year, extra_text])

def random_time(start_time, end_time):
    start_hour, start_minute = start_time.hour, start_time.minute
    end_hour, end_minute = end_time.hour, end_time.minute

    random_hour = random.randint(start_hour, end_hour)
    if random_hour == start_hour:
        random_minute = random.randint(start_minute, 59)
    elif random_hour == end_hour:
        random_minute = random.randint(0, end_minute)
    else:
        random_minute = random.randint(0, 59)

    return f"{random_hour:02d}:{random_minute:02d}"

def generate_schedule():
    global editable_schedule
    editable_schedule = []

    meno = entry_meno.get()
    rodne_cislo = entry_rc.get()
    adresa = entry_adresa.get()
    poistovna = entry_poistovna.get()

    start_date = date_start.get_date()
    end_date = date_end.get_date()
    start_time = entry_start_time.get()
    end_time = entry_end_time.get()
    write_start_time = write_entry_start_time.get()
    write_end_time = write_entry_end_time.get()
    schedule_option = schedule_var.get()

    extra_text = text_extra.get("1.0", "end-1c")
    name_worker = name_worker_extra.get()

    if not meno or not rodne_cislo or not adresa or not poistovna or not start_date or not end_date or not start_time or not end_time or not extra_text or not name_worker or not write_start_time or not write_end_time:
        messagebox.showwarning("Chyba", "Prosím, vyplňte všetky povinné polia.")
        return

    try:
        start_time_dt = datetime.datetime.strptime(start_time, "%H:%M").time()
        end_time_dt = datetime.datetime.strptime(end_time, "%H:%M").time()
        write_start_time_dt = datetime.datetime.strptime(write_start_time, "%H:%M").time()
        write_end_time_dt = datetime.datetime.strptime(write_end_time, "%H:%M").time()
    except ValueError:
        messagebox.showwarning("Chyba", "Čas musí byť vo formáte HH:MM (napr. 08:30).")
        return
    
    current_date = start_date
    while current_date <= end_date:
        weekday = current_date.weekday()  # Monday = 0, Sunday = 6

        if schedule_option == "Každý deň":
            editable_schedule.append([current_date.strftime('%d.%m.%Y'), random_time(start_time_dt, end_time_dt), random_time(write_start_time_dt, write_end_time_dt), extra_text])
        elif schedule_option == "Každý pracovný deň" and weekday < 5:
            editable_schedule.append([current_date.strftime('%d.%m.%Y'), random_time(start_time_dt, end_time_dt), random_time(write_start_time_dt, write_end_time_dt), extra_text])
        elif schedule_option == "3x v týždni":
            if weekday in [0, 2, 4]:
                editable_schedule.append([current_date.strftime('%d.%m.%Y'), random_time(start_time_dt, end_time_dt), random_time(write_start_time_dt, write_end_time_dt), extra_text])

        current_date += datetime.timedelta(days=1)

    if not editable_schedule:
        messagebox.showwarning("Chyba", "Neboli vygenerované žiadne dátumy.")
        return

    save_patient_data()
    save_entry_data()
    open_preview_window()

    # Generate scheduled dates based on user input

def open_preview_window():
    preview_win = tk.Toplevel(root)
    preview_win.title("Náhľad rozvrhu")
    preview_win.geometry("700x400")

    # Table with an extra column for Write Time
    columns = ("Dátum", "Čas ZS", "Čas Zápisu", "Text")
    tree = ttk.Treeview(preview_win, columns=columns, show="headings", height=15)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=160)  # Adjust width for better visibility

    # Insert data (including Write Time)
    for row in editable_schedule:
        tree.insert("", "end", values=row)

    tree.pack(expand=True, fill="both", padx=10, pady=10)

    def on_double_click(event):
        """ Enables in-place editing of the Treeview table. """
        selected_item = tree.selection()
        if not selected_item:
            return

        item = selected_item[0]
        col_id = tree.identify_column(event.x)  # Get clicked column (e.g., #1, #2, #3)
        col_index = int(col_id[1:]) - 1  # Convert column ID to index (0=Date, 1=Time, 2=Write Time, 3=Text)

        x, y, width, height = tree.bbox(item, col_index)  # Get cell position
        value = tree.item(item, "values")[col_index]  # Get current value

        entry_edit = tk.Entry(preview_win)
        entry_edit.insert(0, value)
        entry_edit.place(x=x, y=y + 25, width=width, height=height)  # Position the entry over the cell
        entry_edit.focus()

        def save_edit(event):
            """ Saves the new value when user presses Enter. """
            new_value = entry_edit.get()
            current_values = list(tree.item(item, "values"))
            current_values[col_index] = new_value
            tree.item(item, values=current_values)  # Update row in Treeview
            entry_edit.destroy()

        entry_edit.bind("<Return>", save_edit)
        entry_edit.bind("<FocusOut>", lambda event: entry_edit.destroy())  # Remove entry if user clicks away

    tree.bind("<Double-1>", on_double_click)  # Enable in-place editing

    def delete_selected():
        selected_items = tree.selection()
        for item in selected_items:
            tree.delete(item)

    def save_edits():
        global editable_schedule
        editable_schedule = []
        for item in tree.get_children():
            values = tree.item(item, "values")
            editable_schedule.append(list(values))
        
        generate_pdf()

    btn_frame = tk.Frame(preview_win)
    btn_frame.pack(fill="x", padx=10, pady=5)

    btn_delete = tk.Button(btn_frame, text="Vymazať vybrané", command=delete_selected)
    btn_delete.pack(side="left", padx=5)

    btn_save = tk.Button(btn_frame, text="Generovať PDF", command=save_edits)
    btn_save.pack(side="right", padx=5)

def open_pdf(pdf_path):
    if platform.system() == "Windows":
        os.system(f'start "" "{pdf_path}"')  # Windows
    elif platform.system() == "Darwin":  # macOS
        os.system(f"open '{pdf_path}'")  # macOS
    else:
        messagebox.showinfo("Otvorte manuálne", f"PDF bolo uložené: {pdf_path}")

def sanitize_filename(name):
    """Removes special characters from filenames to prevent Windows errors."""
    return re.sub(r'[<>:"/\\|?*]', '', name)

def generate_pdf():
    if not editable_schedule:
        messagebox.showwarning("Chyba", "Najskôr vygenerujte a upravte plán.")
        return

    if platform.system() == "Windows":
        documents_path = os.path.join(os.environ["USERPROFILE"], "Documents", "ADOS")
    else:
        documents_path = os.path.expanduser("~/Documents/ADOS")

    os.makedirs(documents_path, exist_ok=True)

    # Extract month and year from the first scheduled date
    first_date = editable_schedule[0][0]  # Get first date (format: 'dd.mm.yyyy')
    try:
        parsed_date = datetime.datetime.strptime(first_date, "%d.%m.%Y")
        month_year = parsed_date.strftime("%m-%Y")  # Convert to MM-YYYY format
    except ValueError:
        messagebox.showerror("Chyba", "Neplatný formát dátumu.")
        return

    # Create a valid filename
    name = sanitize_filename(entry_meno.get().replace(" ", "_"))
    pdf_filename = f"{month_year}_{name}.pdf"

    # **Fix: Save file to Documents/ADOS instead of the current directory**
    pdf_path = os.path.join(documents_path, pdf_filename)

    # Create the PDF
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    page_number = 1

    def replace_slovak_chars(text):
        """Replaces Slovak characters that might not render correctly in the PDF."""
        replacements = {
            "č": "c", "š": "s", "ť": "t", "ž": "z", "ý": "y",
            "á": "a", "í": "i", "é": "e", "ú": "u", "ľ": "l",
            "ď": "d", "ň": "n", "ó": "o", "ř": "r", "ě": "e"
        }
        return "".join(replacements.get(char, char) for char in text)

    def draw_header():
        """Draws patient details at the top of each page to match the format."""
        c.setFont("Helvetica-Bold", 14)
        c.drawString(180, height - 40, replace_slovak_chars("DEKURZ OSETROVATELSKEJ STAROSTLIVOSTI"))

        c.setFont("Helvetica", 10)
        c.drawString(50, height - 60, replace_slovak_chars("Andramed, o.z."))
        c.drawString(50, height - 75, replace_slovak_chars("SNP 8, 98601 Fiľakovo"))
        c.drawString(50, height - 90, replace_slovak_chars("ADOS"))

        # Line Separator
        c.line(50, height - 100, width - 50, height - 100)

        # Patient Information
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, height - 120, replace_slovak_chars("Meno, priezvisko, titul pacienta/pacientky:"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 150, entry_meno.get())

        c.setFont("Helvetica-Bold", 10)
        c.drawString(350, height - 120, replace_slovak_chars("Rodné číslo:"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(350, height - 150, entry_rc.get())

        # Line Separator
        c.line(50, height - 160, width - 50, height - 160)

        # Table Header
        c.setFont("Helvetica-Bold", 10)

    def draw_footer(page_num):
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 50, 30, f"Strana {page_num}") 

    draw_header()
    c.setFont("Helvetica", 10)

    # Start position for text
    y_position = height - 180  

    for date, zs_time, write_time, text in editable_schedule:
        c.setFont("Helvetica", 10)
        c.drawString(50, y_position, replace_slovak_chars(f'Dátum a čas zápisu: {date},  {write_time}'))
        y_position -= 30

        # Wrap text
        text_lines = simpleSplit(replace_slovak_chars(f'{zs_time}: {text}'), "Helvetica", 10, width - 100)
        for line in text_lines:
            c.drawString(50, y_position, line)
            y_position -= 15

        # Nurse's Signature
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y_position, name_worker_extra.get())
        c.setFont("Helvetica", 10)
        c.drawString(200, y_position, "Podpis:")
        y_position -= 15

        # Draw separator line
        c.setStrokeColor(colors.black)
        c.line(50, y_position, width - 50, y_position)
        y_position -= 20

        # Ensure new page if needed
        if y_position < 50:
            c.showPage()
            draw_header()
            y_position = height - 180

    draw_footer(page_number)

    c.save()
    open_pdf(pdf_path)

def find_patient_data():
    rodne_cislo = entry_rc.get().strip()

    if not rodne_cislo:
        messagebox.showwarning("Chyba", "Zadajte rodné číslo pacienta.")
        return

    if platform.system() == "Windows":
        documents_path = os.path.join(os.environ["USERPROFILE"], "Documents", "ADOS")  # Windows path
    else:
        documents_path = os.path.expanduser("~/Documents/ADOS")

    csv_file = os.path.join(documents_path, "pacienti_databaza.csv")

    if not os.path.isfile(csv_file):
        messagebox.showwarning("Chyba", "Databáza pacientov neexistuje.")
        return

    # Search for patient in CSV
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip header
        for row in reader:
            if len(row) >= 2 and row[1] == rodne_cislo:
                # Populate fields with found data
                entry_meno.delete(0, tk.END)
                entry_meno.insert(0, row[0])

                entry_adresa.delete(0, tk.END)
                entry_adresa.insert(0, row[2])

                entry_poistovna.delete(0, tk.END)
                entry_poistovna.insert(0, row[3])

                return
    
    messagebox.showwarning("Chyba", "Pacient s týmto rodným číslom nebol nájdený.")

def open_records_window():
    """Opens a new window with all records for a given Rodné číslo, sorted by date."""
    
    rodne_cislo = entry_rc.get().strip()
    
    if not rodne_cislo:
        messagebox.showwarning("Chyba", "Zadajte rodné číslo pacienta.")
        return

    # Define the file path
    if platform.system() == "Windows":
        documents_path = os.path.join(os.environ["USERPROFILE"], "Documents", "ADOS")
    else:
        documents_path = os.path.expanduser("~/Documents/ADOS")
    
    csv_file = os.path.join(documents_path, "nalezy_databaza.csv")

    if not os.path.isfile(csv_file):
        messagebox.showwarning("Chyba", "Databáza záznamov neexistuje.")
        return

    # Read and filter records
    records = []
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip header
        for row in reader:
            if len(row) >= 3 and row[0] == rodne_cislo:
                try:
                    date_obj = datetime.datetime.strptime(row[1], "%m/%Y")  # Convert to date object
                    records.append((date_obj, row[1], row[2]))  # Store as (date_obj, formatted date, text)
                except ValueError:
                    continue  # Skip invalid rows

    if not records:
        messagebox.showwarning("Chyba", "Pre toto rodné číslo neboli nájdené žiadne záznamy.")
        return

    # Sort records by date (oldest to newest)
    records.sort(key=lambda x: x[0])

    # Create a new window
    records_win = tk.Toplevel(root)
    records_win.title(f"Záznamy pre {rodne_cislo}")
    records_win.geometry("500x400")

    # Scrollable Frame
    container = tk.Frame(records_win)
    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    container.pack(fill="both", expand=True)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Create headers
    tk.Label(scrollable_frame, text="Dátum (Mesiac/Rok)", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
    tk.Label(scrollable_frame, text="Nález", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=10, pady=5, sticky="w")

    # Add records to the window
    for i, (_, date, text) in enumerate(records, start=1):
        tk.Label(scrollable_frame, text=date).grid(row=i, column=0, padx=10, pady=2, sticky="w")
        tk.Label(scrollable_frame, text=text, wraplength=300, justify="left").grid(row=i, column=1, padx=10, pady=2, sticky="w")




# GUI Setup
root = tk.Tk()
root.title("ADOS")
root.geometry("800x600")

# Create a Frame for the form
form_frame = tk.Frame(root)
form_frame.pack(pady=10, padx=10, fill="x")

# Meno
tk.Label(form_frame, text="Meno:", width=20, anchor="e").grid(row=0, column=0, padx=5, pady=5)
entry_meno = tk.Entry(form_frame, width=40)
entry_meno.grid(row=0, column=1, padx=5, pady=5)

# Rodné číslo
tk.Label(form_frame, text="Rodné číslo:", width=20, anchor="e").grid(row=1, column=0, padx=5, pady=5)

# Frame for Entry + Button (inside the same grid row)
rc_frame = tk.Frame(form_frame)
rc_frame.grid(row=1, column=1, padx=5, pady=5, sticky="w")

rc_var = tk.StringVar()
entry_rc = tk.Entry(rc_frame, textvariable=rc_var, width=30)
entry_rc.pack(side="left", padx=(0, 5))
entry_rc.bind("<KeyRelease>", lambda event: rc_change(entry_rc, rc_var))

# Find Patient Button inside the same field
btn_search = tk.Button(rc_frame, text="Hľadať", command=find_patient_data)
btn_search.pack(side="left")

# Adresa
tk.Label(form_frame, text="Adresa:", width=20, anchor="e").grid(row=2, column=0, padx=5, pady=5)
entry_adresa = tk.Entry(form_frame, width=40)
entry_adresa.grid(row=2, column=1, padx=5, pady=5)

# Zdravotná poisťovňa
tk.Label(form_frame, text="Zdravotná poisťovňa:", width=20, anchor="e").grid(row=3, column=0, padx=5, pady=5)
entry_poistovna = tk.Entry(form_frame, width=40)
entry_poistovna.grid(row=3, column=1, padx=5, pady=5)


ttk.Separator(root, orient="horizontal").pack(fill="x", padx=10, pady=5)

# Frame for Date & Time Selection
datetime_frame = tk.Frame(root)
datetime_frame.pack(pady=10, padx=10, fill="x")

# Začiatok (Start Date)
tk.Label(datetime_frame, text="Začiatok:", width=20, anchor="e").grid(row=0, column=0, padx=5, pady=5)
date_start = DateEntry(datetime_frame, width=15, background="grey", foreground="black", borderwidth=2, date_pattern="dd/MM/yyyy")
date_start.grid(row=0, column=1, padx=5, pady=5)

# Koniec (End Date)
tk.Label(datetime_frame, text="Koniec:", width=20, anchor="e").grid(row=0, column=2, padx=5, pady=5)
date_end = DateEntry(datetime_frame, width=15, background="grey", foreground="black", borderwidth=2, date_pattern="dd/MM/yyyy")
date_end.grid(row=0, column=3, padx=5, pady=5)

# Čas poskytnutia ZS (Medical Service Time)
tk.Label(datetime_frame, text="Čas poskytnutia ZS od:", width=20, anchor="e").grid(row=2, column=0, padx=5, pady=5)
zs_start_time_var = tk.StringVar(value="08:00")
entry_start_time = tk.Entry(datetime_frame, textvariable=zs_start_time_var, width=15)
entry_start_time.grid(row=2, column=1, padx=5, pady=5)
entry_start_time.bind("<KeyRelease>", lambda event: time_change(entry_start_time, zs_start_time_var))

tk.Label(datetime_frame, text="Čas poskytnutia ZS do:", width=20, anchor="e").grid(row=2, column=2, padx=5, pady=5)
zs_end_time_var = tk.StringVar(value="13:00")
entry_end_time = tk.Entry(datetime_frame, textvariable=zs_end_time_var, width=15)
entry_end_time.grid(row=2, column=3, padx=5, pady=5)
entry_end_time.bind("<KeyRelease>", lambda event: time_change(entry_end_time, zs_end_time_var))

# Čas zápisu (Write Time)
tk.Label(datetime_frame, text="Čas zápisu od:", width=20, anchor="e").grid(row=3, column=0, padx=5, pady=5)
write_start_time_var = tk.StringVar(value="13:00")
write_entry_start_time = tk.Entry(datetime_frame, textvariable=write_start_time_var, width=15)
write_entry_start_time.grid(row=3, column=1, padx=5, pady=5)
write_entry_start_time.bind("<KeyRelease>", lambda event: time_change(write_entry_start_time, write_start_time_var))

tk.Label(datetime_frame, text="Čas zápisu do:", width=20, anchor="e").grid(row=3, column=2, padx=5, pady=5)
write_end_time_var = tk.StringVar(value="15:00")
write_entry_end_time = tk.Entry(datetime_frame, textvariable=write_end_time_var, width=15)
write_entry_end_time.grid(row=3, column=3, padx=5, pady=5)
write_entry_end_time.bind("<KeyRelease>", lambda event: time_change(write_entry_end_time, write_end_time_var))


# Opakovanie (Repetition)
tk.Label(datetime_frame, text="Opakovanie:", width=20, anchor="e").grid(row=4, column=0, padx=5, pady=5)
schedule_var = tk.StringVar(value="Každý deň")
schedule_options = ["Každý deň", "Každý pracovný deň", "3x v týždni"]
schedule_dropdown = ttk.Combobox(datetime_frame, textvariable=schedule_var, values=schedule_options, width=15)
schedule_dropdown.grid(row=4, column=1, padx=5, pady=5)


ttk.Separator(root, orient="horizontal").pack(fill="x", padx=10, pady=5)

worker_frame = tk.Frame(root)
worker_frame.pack(pady=5, fill="x")
tk.Label(worker_frame, text="Meno vypĺňajúceho:", width=20, anchor="e").grid(row=0, column=0, padx=5, pady=5)
name_worker_extra = tk.Entry(worker_frame, width=40)
name_worker_extra.grid(row=0, column=1, padx=5, pady=5)

# Frame for "Nález" Input
finding_frame = tk.Frame(root)
finding_frame.pack(pady=5, fill="x")
tk.Label(finding_frame, text="Nález:", width=20, anchor="ne").grid(row=0, column=0, padx=5, pady=5, sticky="ne")
text_extra = tk.Text(finding_frame, height=5, width=50, wrap="word")
text_extra.grid(row=0, column=1, padx=5, pady=5)


tk.Button(root, text="Zobraziť nálezy pacienta", command=open_records_window).pack(pady=5)


tk.Button(root, text="Náhľad rozvrhu", command=generate_schedule).pack(pady=10)

root.mainloop()
