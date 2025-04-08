function postMonth() {
    let nurseId = document.getElementById("nurse_id").value;
    let monthInput = document.getElementById("month").value;
    let zsStartTime = document.getElementById("zs_start_time").value;
    let zsEndTime = document.getElementById("zs_end_time").value;
    let writeStartTime = document.getElementById("write_start_time").value;
    let writeEndTime = document.getElementById("write_end_time").value;

    if (!monthInput || !nurseId) {
        alert("Mesiac a sestra sú povinné!");
        return;
    }

    let postData = {
        nurse: nurseId,
        month: monthInput,
        zs_start_time: zsStartTime,
        zs_end_time: zsEndTime,
        write_start_time: writeStartTime,
        write_end_time: writeEndTime
    };

    fetch("/month", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(postData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.redirect) {
                window.location.href = data.redirect;
            } else if (data.error) {
                alert("Chyba: " + data.error);
            }
        })
        .catch(error => {
            console.error("Chyba pri odoslaní dát:", error);
            alert("Chyba pri odoslaní dát!");
        });
}

function generate(startDate, endDate, frequency, exceptions = []) {
    console.log("Inside generateSchedule Function");
    console.log("Start Date:", startDate);
    console.log("End Date:", endDate);
    console.log("Frequency:", frequency);
    console.log("Exceptions:", exceptions);

    if (!startDate || !endDate) {
        console.error("Invalid startDate or endDate!");
        return [];
    }

    let scheduleDates = [];
    let currentDate = new Date(startDate);
    let lastDate = new Date(endDate);

    // Normalize to midnight (local time)
    currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate());
    lastDate = new Date(lastDate.getFullYear(), lastDate.getMonth(), lastDate.getDate());

    while (currentDate <= lastDate) {
        const dayOfWeek = currentDate.getDay();
        const dateStr = formatLocalDate(currentDate);

        if (!exceptions.includes(dateStr)) {
            if (frequency === "daily") {
                scheduleDates.push(dateStr);
            } else if (frequency === "weekday" && dayOfWeek !== 0 && dayOfWeek !== 6) {
                scheduleDates.push(dateStr);
            } else if (frequency === "3x_week" && [1, 3, 5].includes(dayOfWeek)) {
                scheduleDates.push(dateStr);
            }
        }

        currentDate.setDate(currentDate.getDate() + 1);
    }

    console.log("Generated Schedule Dates (without exceptions):", scheduleDates);
    return scheduleDates;
}

function formatLocalDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
}



function getFlatpickrDate(inputId) {
    let picker = document.getElementById(inputId)?._flatpickr;
    if (picker && picker.selectedDates.length > 0) {
        // This is already a Date object in local time
        let selectedDate = picker.selectedDates[0];

        // Don't create a new Date or adjust time — just extract values directly
        const year = selectedDate.getFullYear();
        const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
        const day = String(selectedDate.getDate()).padStart(2, '0');

        return `${year}-${month}-${day}`;
    }
    return null;
}




function postPatientAndSchedule() {
    let patientData = {
        meno: document.getElementById("meno").value,
        rodne_cislo: document.getElementById("rodne_cislo").value,
        adresa: document.getElementById("adresa").value,
        poistovna: document.getElementById("poistovna").value,
        sestra: document.getElementById("nurse_id").value,
        ados: document.getElementById("company").value
    };

    fetch("/save_patient", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(patientData)
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert("Chyba pri ukladaní pacienta!");
                return;
            }

            let patientId = data.patient_id;
            let dateStart = getFlatpickrDate("date_start");
            let dateEnd = getFlatpickrDate("date_end");
            console.log("startDate:", dateStart);
            console.log("endDate:", dateEnd)
            let frequency = document.getElementById("schedule").value;
            let exceptionDates = [];

            const exceptionsPicker = document.getElementById("exceptions")._flatpickr;
            if (exceptionsPicker) {
                exceptionDates = exceptionsPicker.selectedDates.map(date =>
                    date.toLocaleDateString("sv-SE")
                );
            }

            if (!patientId || !dateStart || !dateEnd) {
                alert("Vyplňte všetky povinné polia!");
                return;
            }

            let dateObj = new Date(dateStart);
            let year = dateObj.getFullYear();
            let month = (dateObj.getMonth() + 1).toString().padStart(2, "0");

            console.log("")

            let schedule = generate(dateStart, dateEnd, frequency, exceptionDates);

            let scheduleData = {
                sestra: document.getElementById("nurse_id").value,
                patient_id: patientId,
                year: parseInt(year, 10),
                month: parseInt(month, 10),
                schedule: schedule
            };

            return fetch("/insert_schedule", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(scheduleData)
            });
        })
        .then(response => response.json())
        .then(data => {
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                alert("Chyba pri ukladaní harmonogramu.");
            }
        })
        .catch(error => {
            console.error("Chyba pri ukladaní pacienta alebo harmonogramu:", error);
        });
}



