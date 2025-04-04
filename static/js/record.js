const transactionForm = document.getElementById('transactionForm');

transactionForm.addEventListener('submit', async event =>{
    event.preventDefault();
    if (!transactionForm.checkValidity()) {
        transactionForm.classList.add('was-validated');
        return;
    }

    const memberName = document.getElementById('memberName').value;
    const amount = document.getElementById('amount').value;
    const paymentType = document.getElementById('paymentType').value;
    const date = document.getElementById('date').value;
    const notify = document.getElementById('sms');
    let sms = false;
    let sender_id = null;
    if(notify.checked){
        sms = true;
        sender_id = document.getElementById('senderIdTable').value;
        //notify(memberName,amount,paymentType,date);
    }

    if(memberName === "" || amount ==="" || paymentType === ""){
        //console.log("Something is missing");
        return
    }
    if(date == ''){
        document.getElementById('alertBox').textContent = `Tafadhali hakikisha unaweka tarehe`;
        document.getElementById('alertBox').classList.add('alert-danger');
        document.getElementById('alertBox').classList.remove('d-none');
        return
    }
    disabler(true);
    fetch('/record_transaction',{
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({memberName,amount,paymentType,date})
    })
    .then(response => response.json())
    .then(data => {
        if(data.error){
            disabler(false);
            document.getElementById('alertBox').textContent = data.error;
            document.getElementById('alertBox').classList.add('alert-danger');
            document.getElementById('alertBox').classList.remove('d-none');
        }
        else{
            if(sms){
                notify_member(memberName,amount,paymentType,date,sender_id);
            }
            else{
                disabler(false);
                document.getElementById('alertBox').textContent = data.message;
                transactionForm.reset();
                document.getElementById('alertBox').classList.add('alert-success');
                document.getElementById('alertBox').classList.remove('d-none'); 
            }
        }
    })
    .catch(error => {
        disabler(false);
        document.getElementById('alertBox').textContent = error;
        document.getElementById('alertBox').classList.add('alert-danger');
        document.getElementById('alertBox').classList.remove('d-none');
    })
})

function notify_member(memberName,amount,paymentType,date,sender_id){
    const isFirstTime = false
    const alertBox = document.getElementById('alertBox');
    var form = document.getElementById('transactionForm');
    fetch('/notify_record',{
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({memberName,amount,paymentType,date,isFirstTime,sender_id})
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
            alertBox.textContent = `Muamala umefanyika kwa mafanikio`;
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
    document.getElementById('memberName').disabled = bool;
    document.getElementById('amount').disabled = bool;
    document.getElementById('paymentType').disabled = bool;
    document.getElementById('date').disabled = bool;
    document.getElementById('sms').disabled = bool;
    document.getElementById('record_muamala').disabled = bool;

    if(bool===true){
        document.getElementById('record_muamala').textContent = `Inarecord muamala...`;
    }
    else{
        document.getElementById('record_muamala').textContent = `Record Muamala`;
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
                alert(data.error);
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