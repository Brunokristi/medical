import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import random
import datetime
import os
import platform
import re


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
    """Generates the list of scheduled dates with random times and opens a preview window."""
    global editable_schedule
    editable_schedule = []

    meno = entry_meno.get()
    rodne_cislo = entry_rc.get()
    adresa = entry_adresa.get()
    poistovna = entry_poistovna.get()

    start_date_str = date_start_var.get()
    end_date_str = date_end_var.get()
    start_time = entry_start_time.get()
    end_time = entry_end_time.get()
    schedule_option = schedule_var.get()

    extra_text = text_extra.get("1.0", "end-1c")
    name_worker = name_worker_extra.get()

    if not meno or not rodne_cislo or not adresa or not poistovna or not start_date_str or not end_date_str or not start_time or not end_time or not extra_text or not name_worker:
        messagebox.showwarning("Chyba", "Prosím, vyplňte všetky povinné polia.")
        return

    # Convert date strings to datetime.date objects
    try:
        start_date = datetime.datetime.strptime(start_date_str, "%d/%m/%Y").date()
        end_date = datetime.datetime.strptime(end_date_str, "%d/%m/%Y").date()
    except ValueError:
        messagebox.showwarning("Chyba", "Dátumy musia byť vo formáte DD/MM/YYYY.")
        return

    # Convert time strings to datetime.time objects
    try:
        start_time_dt = datetime.datetime.strptime(start_time, "%H:%M").time()
        end_time_dt = datetime.datetime.strptime(end_time, "%H:%M").time()
    except ValueError:
        messagebox.showwarning("Chyba", "Čas musí byť vo formáte HH:MM (napr. 08:30).")
        return

    # Generate scheduled dates based on user input
    current_date = start_date
    while current_date <= end_date:
        weekday = current_date.weekday()  # Monday = 0, Sunday = 6

        if schedule_option == "Každý deň":
            editable_schedule.append([current_date.strftime('%d.%m.%Y'), random_time(start_time_dt, end_time_dt), extra_text])
        elif schedule_option == "Každý pracovný deň" and weekday < 5:
            editable_schedule.append([current_date.strftime('%d.%m.%Y'), random_time(start_time_dt, end_time_dt), extra_text])
        elif schedule_option == "3x v týždni":
            if weekday in [0, 2, 4]:
                editable_schedule.append([current_date.strftime('%d.%m.%Y'), random_time(start_time_dt, end_time_dt), extra_text])

        current_date += datetime.timedelta(days=1)

    if not editable_schedule:
        messagebox.showwarning("Chyba", "Neboli vygenerované žiadne dátumy.")
        return

    open_preview_window()

def open_preview_window():
    """Opens a preview window with an editable schedule table."""
    preview_win = tk.Toplevel(root)
    preview_win.title("Náhľad rozvrhu")
    preview_win.geometry("600x400")

    # Table
    columns = ("Dátum", "Čas", "Text")
    tree = ttk.Treeview(preview_win, columns=columns, show="headings", height=15)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=180)

    # Insert data
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
        col_index = int(col_id[1:]) - 1  # Convert column ID to index (0=Date, 1=Time, 2=Text)

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

    tree.bind("<Double-1>", on_double_click)  # Bind double-click to enable editing

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

    def replace_slovak_chars(text):
        """Replaces Slovak characters that might not render correctly in the PDF."""
        replacements = {
            "č": "c", "š": "s", "ť": "t", "ž": "z", "ý": "y",
            "á": "a", "í": "i", "é": "e", "ú": "u", "ľ": "l",
            "ď": "d", "ň": "n", "ó": "o", "ř": "r", "ě": "e"
        }
        return "".join(replacements.get(char, char) for char in text)

    def draw_header():
        """Draws patient details at the top of each page."""
        c.setFont("Helvetica", 12)

        meno = replace_slovak_chars(entry_meno.get())
        rc = replace_slovak_chars(entry_rc.get())
        adresa = replace_slovak_chars(entry_adresa.get())
        poistovna = replace_slovak_chars(entry_poistovna.get())

        c.drawString(50, height - 50, f"Meno: {meno}")
        c.drawString(250, height - 50, f"Rodné císlo: {rc}")
        c.drawString(50, height - 70, f"Adresa: {adresa}")
        c.drawString(250, height - 70, f"Zdravotná poistovna: {poistovna}")

        # Draw separator line
        c.line(50, height - 80, width - 50, height - 80)

    draw_header()
    c.setFont("Helvetica", 11)

    # Start position for text
    y_position = height - 110  

    for date, time, text in editable_schedule:

        c.setFont("Helvetica", 11)
        c.drawString(50, y_position, f"{date}    {time}    {replace_slovak_chars(name_worker_extra.get())}")
        y_position -= 40  # Space before next entry

        # Print the extra text (separate for each entry)
        c.drawString(50, y_position, replace_slovak_chars(text))
        y_position -= 20  

        # Draw separator line
        c.line(50, y_position, width - 50, y_position)
        y_position -= 20

        # Ensure new page if needed
        if y_position < 50:
            c.showPage()
            draw_header()
            y_position = height - 110

    c.save()
    open_pdf(pdf_path)



# GUI Setup
root = tk.Tk()
root.title("Formulár na tlač")
root.geometry("450x850")

tk.Label(root, text="Pacient", font=("Arial", 12, "bold")).pack(pady=(10, 2))
ttk.Separator(root, orient="horizontal").pack(fill="x", padx=10, pady=5)

# Inputs
tk.Label(root, text="Meno:").pack()
entry_meno = tk.Entry(root, width=40)
entry_meno.pack()

tk.Label(root, text="Rodné číslo:").pack()
rc_var = tk.StringVar()
entry_rc = tk.Entry(root, textvariable=rc_var, width=40)
entry_rc.pack()
entry_rc.bind("<KeyRelease>", lambda event: rc_change(entry_rc, rc_var))  # Format input dynamically

tk.Label(root, text="Adresa:").pack()
entry_adresa = tk.Entry(root, width=40)
entry_adresa.pack()

tk.Label(root, text="Zdravotná poisťovňa:").pack()
entry_poistovna = tk.Entry(root, width=40)
entry_poistovna.pack()

tk.Label(root, text="Výber dátumu a času", font=("Arial", 12, "bold")).pack(pady=(15, 2))
ttk.Separator(root, orient="horizontal").pack(fill="x", padx=10, pady=5)

tk.Label(root, text="Začiatok:").pack()
date_start_var = tk.StringVar(value=today)  # Pre-fill today's date
entry_start = tk.Entry(root, textvariable=date_start_var, width=15)
entry_start.pack()
entry_start.bind("<KeyRelease>", lambda event: date_change(entry_start, date_start_var))  # Format input dynamically

tk.Label(root, text="Koniec:").pack()
date_end_var = tk.StringVar(value=today)  # Pre-fill today's date
entry_end = tk.Entry(root, textvariable=date_end_var, width=15)
entry_end.pack()
entry_end.bind("<KeyRelease>", lambda event: date_change(entry_end, date_end_var))  # Format input dynamically

tk.Label(root, text="Odkedy (hh:mm):").pack()
start_time_var = tk.StringVar(value="08:00")  # Default to 08:00
entry_start_time = tk.Entry(root, textvariable=start_time_var, width=15)
entry_start_time.pack()
entry_start_time.bind("<KeyRelease>", lambda event: time_change(entry_start_time, start_time_var))  # Format input dynamically

# End Time
tk.Label(root, text="Dokedy (hh:mm):").pack()
end_time_var = tk.StringVar(value="13:00")  # Default to 13:00
entry_end_time = tk.Entry(root, textvariable=end_time_var, width=15)
entry_end_time.pack()
entry_end_time.bind("<KeyRelease>", lambda event: time_change(entry_end_time, end_time_var))  # Format input dynamically

tk.Label(root, text="Opakovanie:").pack()
schedule_var = tk.StringVar(value="Každý deň")
schedule_options = ["Každý deň", "Každý pracovný deň", "3x v týždni"]
schedule_dropdown = ttk.Combobox(root, textvariable=schedule_var, values=schedule_options, width=15)
schedule_dropdown.pack()

tk.Label(root, text="Informácie", font=("Arial", 12, "bold")).pack(pady=(15, 2))
ttk.Separator(root, orient="horizontal").pack(fill="x", padx=10, pady=5)

tk.Label(root, text="Doplnkový text:").pack()
text_extra = tk.Text(root, height=10, width=50, wrap="word") 
text_extra.pack(padx=10, pady=5)

tk.Label(root, text="Meno vypĺňajúceho:").pack()
name_worker_extra = tk.Entry(root, width=40)
name_worker_extra.pack()

tk.Button(root, text="Náhľad rozvrhu", command=generate_schedule).pack(pady=10)

root.mainloop()
