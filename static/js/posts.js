function postMonth() {
    var nurseId = document.getElementById("nurse_id").value;
    var monthInput = document.getElementById("month").value;
    var zsStartTime = document.getElementById("zs_start_time").value;
    var zsEndTime = document.getElementById("zs_end_time").value;
    var writeStartTime = document.getElementById("write_start_time").value;
    var writeEndTime = document.getElementById("write_end_time").value;

    if (!monthInput || !nurseId) {
        alert("Prosím vyberte sestru a mesiac.");
        return;
    }

    var [year, month] = monthInput.split("-");

    var postData = {
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
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                return response.json();
            }
        })
        .catch(error => {
            console.error("Chyba pri odoslaní dát:", error);
            alert("Chyba pri odoslaní dát!");
        });
}

function postPatient() {
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
            alert(data.message);
        })
        .catch(error => {
            console.error("Chyba pri ukladaní pacienta:", error);
        });
}