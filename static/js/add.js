document.addEventListener('DOMContentLoaded', function () {
    'use strict';
    var form = document.getElementById('memberForm');

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }

        const name = document.getElementById('name').value.trim();
        let phoneNumber = document.getElementById('phone').value.trim();
        const promise_amount = document.getElementById('promise_amount').value.trim();
        const cash_amount = document.getElementById('cash_amount').value.trim();
        let date = document.getElementById('date').value;
        const alertBox = document.getElementById('alertBox');
        const notify = document.getElementById('sms');
        let sms = false;
        let sender_id = null;
        if(notify.checked){
            sms = true;
            sender_id = document.getElementById('senderIdTable').value;
        }

        if(phoneNumber === ""){
            phoneNumber = null;
        }
        else if(phoneNumber !== "" && phoneNumber.length != 10){
            alertBox.textContent = `Tafadhali hakikisha namba ulizoweka ina tarakimu 10`;
            alertBox.classList.add('alert-danger');
            alertBox.classList.remove('d-none');
            return;
        }
        
        if(phoneNumber !== "" && !phoneNumber.startsWith('0')){
            alertBox.textContent = `Tafadhali hakikisha namba uliyoweka inaanzia na 0`;
            alertBox.classList.add('alert-danger');
            alertBox.classList.remove('d-none');
            return
        }

        if (name === ""  || promise_amount === "" || cash_amount === "") {
            return;
        }

        if (date === '') {
            alertBox.textContent = `Tafadhali hakikisha unaweka tarehe`;
            alertBox.classList.add('alert-danger');
            alertBox.classList.remove('d-none');
            return;
        }

        try {
            disabler(true);
            const response = await fetch('/add_member', {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, phoneNumber, promise_amount, cash_amount,date})
            });

            const data = await response.json();

            if (data.error) {
                disabler(false);
                alertBox.textContent = data.error;
                alertBox.classList.add('alert-danger');
                alertBox.classList.remove('d-none');
            } else {
                if(sms && phoneNumber != null){
                    await notify_member(name,phoneNumber,promise_amount,cash_amount,date,sender_id);
                }
                else{
                    disabler(false);
                    alertBox.textContent = data.message;
                    alertBox.classList.add('alert-success');
                    alertBox.classList.remove('d-none');
                    form.reset();
                    form.classList.remove('was-validated');
                }
            }
        } catch (error) {
            disabler(false);
            alertBox.textContent = "An error occurred while submitting the form.";
            alertBox.classList.add('alert-danger');
            alertBox.classList.remove('d-none');
        }
    });
});

function notify_member(name,phoneNumber,promise_amount,cash_amount,date,sender_id){
    const isFirstTime = true;
    const alertBox = document.getElementById('alertBox');
    var form = document.getElementById('memberForm');
    fetch('/notify_record',{
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name,phoneNumber,promise_amount,cash_amount,date,isFirstTime,sender_id})
    })
    .then(response => response.json())
    .then(data => {
        disabler(false);
        if(!data.error){
            alertBox.textContent = `Mchangiaji ameongezwa kwa mafanikio`;
            showToast(data.message);
            alertBox.classList.add('alert-success');
            alertBox.classList.remove('d-none');
            form.reset();
            form.classList.remove('was-validated');
        }
        else{
            alertBox.textContent = `Mchangiaji ameongezwa kwa mafanikio lakini`;
            showToast(data.error);
            alertBox.classList.add('alert-success');
            alertBox.classList.remove('d-none');
            form.reset();
            form.classList.remove('was-validated');
        }
        
    }
        
    )
}

function disabler(bool){
    document.getElementById('name').disabled = bool;
    document.getElementById('phone').disabled = bool;
    document.getElementById('promise_amount').disabled = bool;
    document.getElementById('cash_amount').disabled = bool;
    document.getElementById('date').disabled = bool;
    document.getElementById('sms').disabled= bool;
    document.getElementById('kusanya').disabled = bool;

    if(bool === true){
        document.getElementById('kusanya').textContent = `Inakusanya....`;
    }
    else{
        document.getElementById('kusanya').textContent = `Kusanya`;
    }
}

const notify = document.getElementById('sms');
notify.addEventListener('change',()=> {
    const SenderIDS = document.getElementById('senderIdTable');
    if(notify.checked){
        var myModal = new bootstrap.Modal(document.getElementById('smsModal'));
        myModal.show();
        document.getElementById('SIT').classList.remove('d-none');
        SenderIDS.innerHTML = ''
        fetch('/get_sender_ids',{
            method: 'GET',
            headers: {'Content-Type': "application/json"}
        })
        .then(res => res.json())
        .then(data => {
            console.log(data);
            if(data.error){
                showToast(data.error);
            }
            data.forEach(id => {
                const option = `
                <option value="${id}">${id}</option>
                `
                SenderIDS.innerHTML += option;
            })
        })
    }
    else{
        document.getElementById('SIT').classList.add('d-none');
    }
}) 
function showToast(message) {
    document.getElementById('toastAlertMessage').innerText = message;
    let toast = new bootstrap.Toast(document.getElementById('toastAlert'));
    toast.show();
}
