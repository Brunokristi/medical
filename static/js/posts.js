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
        .catch(error => {
            console.error("Chyba pri ukladaní pacienta:", error);
        });
}