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
                window.location.href = data.redirect;  // ✅ Redirect if the month exists
            } else if (data.error) {
                alert("Chyba: " + data.error);
            }
        })
        .catch(error => {
            console.error("Chyba pri odoslaní dát:", error);
            alert("Chyba pri odoslaní dát!");
        });
}

function generateSchedule(startDate, endDate, frequency) {
    let scheduleDates = [];
    let currentDate = new Date(startDate);

    while (currentDate <= new Date(endDate)) {
        let dayOfWeek = currentDate.getDay(); // 0 = Sunday, 6 = Saturday

        if (frequency === "daily") {
            scheduleDates.push(currentDate.toISOString().split("T")[0]);
        } else if (frequency === "weekday" && dayOfWeek !== 0 && dayOfWeek !== 6) {
            scheduleDates.push(currentDate.toISOString().split("T")[0]);
        } else if (frequency === "3x_week") {
            // Choose Mon, Wed, Fri (1, 3, 5)
            if ([1, 3, 5].includes(dayOfWeek)) {
                scheduleDates.push(currentDate.toISOString().split("T")[0]);
            }
        }

        // Move to next day
        currentDate.setDate(currentDate.getDate() + 1);
    }

    return scheduleDates;
}

function getFlatpickrDate(inputId) {
    let picker = document.getElementById(inputId)?._flatpickr;
    if (picker && picker.selectedDates.length > 0) {
        let selectedDate = picker.selectedDates[0];

        // Correctly format the date in YYYY-MM-DD without UTC shift
        let year = selectedDate.getFullYear();
        let month = (selectedDate.getMonth() + 1).toString().padStart(2, "0"); // Ensure two digits
        let day = (selectedDate.getDate() + 1).toString().padStart(2, "0"); // Add 1 day

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
            let frequency = document.getElementById("schedule").value;

            console.log("Patient ID:", patientId);
            console.log("Start Date:", dateStart);
            console.log("End Date:", dateEnd);
            console.log("Frequency:", frequency);

            if (!patientId || !dateStart || !dateEnd) {
                alert("Vyplňte všetky povinné polia!");
                return;
            }

            let dateObj = new Date(dateStart);

            let year = dateObj.getFullYear();
            let month = String(dateObj.getMonth() + 1).padStart(2, "0");

            let schedule = generateSchedule(dateStart, dateEnd, frequency);

            let scheduleData = {
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
            if (data.success) {
                alert("Pacient a harmonogram boli úspešne pridané!");
            } else {
                alert("Chyba pri ukladaní harmonogramu.");
            }
        })
        .catch(error => {
            console.error("Chyba pri ukladaní pacienta alebo harmonogramu:", error);
        });
}
