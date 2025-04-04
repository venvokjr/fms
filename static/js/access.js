let formerAmount = null;
let formerpaymentType = null;
let formerName = null;
let trans_id = null;

function loadTransactions(sortby){
    fetch('/get_transactions',{
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({sortby})
    })
    .then(response => response.json())
    .then(data => {
       // console.log(data[0])
        let transactionTable = document.getElementById('transactionTable');
        transactionTable.innerHTML = '';
        data.forEach(transcation => {
            const row = `
            <tr> 
                <td>${transcation.id}</td>
                <td>${transcation.name}</td>
                <td>${transcation.amount.toLocaleString()}</td>
                <td>${transcation.paymentType}</td>
                <td>${transcation.date}</td>
                <td style="background-color:hsl(0, 0.00%, 23.10%);"><button data-bs-target="#makeEdits" data-bs-toggle="modal" onclick="Edit('${transcation.name}','${transcation.amount}','${transcation.paymentType}','${transcation.date}','${transcation.id}')" id="makeEdit" style="border: none;font-family: sans-serif;color: hsl(140, 59.20%, 39.40%);background-color: hsl(0, 0.00%, 23.10%);">Fanya Rekebisho</button></td>
                               
            </tr>
            `
            transactionTable.innerHTML += row;
        });
        setTimeout(()=>{
            document.getElementById('spiner-body').style.display = 'none';
            document.getElementById('thebody').style.display = 'block';
        },100);
    })
    .catch(error => {
        document.getElementById('alertBox').textContent = error;
        document.getElementById('alertBox').classList.add('alert-danger');
        document.getElementById('alertBox').classList.remove('d-none');
    })
}

document.getElementById('searchMember').addEventListener('keyup', function () {
    let searchValue = this.value.toLowerCase();
    let rows = document.querySelectorAll('#transactionTable tr');
    
    rows.forEach(row => {
        let name = row.cells[1].textContent.toLowerCase();
        if (name.includes(searchValue)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
            
        }
    });
});

function Edit(name,amount,paymentType,date,transaction_id){
    //kufuta muamala
    document.getElementById('jinalake').textContent = name;
    document.getElementById('aina').textContent = paymentType;
    document.getElementById('hela').textContent = Number(amount).toLocaleString();
    document.getElementById('idyamuamala').textContent = transaction_id


    //kubadili muamala
    editName = null;
    editAmount =  null;
    editPaymentType = null;
    editDate = null;
    formerAmount = null;
    formerpaymentType = null;
    formerName = null;
    trans_id = null;

    formerAmount = amount;
    formerpaymentType = paymentType;
    formerName = name;
    trans_id = transaction_id;

    editName = name;
    editAmount = amount;
    editPaymentType = paymentType;
    editDate = date;

    let fromtransaction_id = document.getElementById('kitambulisho');
    let fromName = document.getElementById('name');
    let fromAmount = document.getElementById('kiasi');
    let fromPaymentType = document.getElementById('paymentType');
    let fromDate = document.getElementById('date');

    fromtransaction_id.textContent = `Namba ya Kitambulisho cha muamala: ${transaction_id}`;
    fromName.value = editName;
    fromAmount.value = editAmount;
    fromPaymentType.value = editPaymentType;
    fromDate.value = editDate
    
}

function deleteTransaction(){
    fetch('/delete_transaction',{
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({trans_id,formerpaymentType})
    })
    .then(response => response.json())
    .then(data => {
        if(!data.error){
            document.getElementById('alertBox').textContent = data.message;
            document.getElementById('alertBox').classList.add('alert-success');
            document.getElementById('alertBox').classList.remove('d-none');
        }
        else{
            document.getElementById('alertBox').textContent = data.error;
            document.getElementById('alertBox').classList.add('alert-danger');
            document.getElementById('alertBox').classList.remove('d-none');            
        }

    })
    .catch(error => {
        document.getElementById('alertBox').textContent = error;
        document.getElementById('alertBox').classList.add('alert-danger');
        document.getElementById('alertBox').classList.remove('d-none');
    })
}


function commitChange() {
    const memberName = document.getElementById('name').value;
    const amount = document.getElementById('kiasi').value;
    const paymentType = document.getElementById('paymentType').value;
    const date = document.getElementById('date').value;
    //console.log(amount);
    if(memberName === "" || amount ==="" || paymentType === ""){
        return
    }
    //console.log(amount);
    if(date == ''){
        document.getElementById('alertBox').textContent = `Tafadhali hakikisha unaweka tarehe`;
        document.getElementById('alertBox').classList.add('alert-danger');
        document.getElementById('alertBox').classList.remove('d-none');
        return
    }
    //console.log(kitambulisho);
    fetch('/editTransaction',{
        method: 'POST',
        headers: { "Content-Type": "application/json"},
        body: JSON.stringify({trans_id,memberName,amount,paymentType,date,formerAmount,formerpaymentType,formerName})
    })
    .then(response => response.json())
    .then(data => {
        if(data.error){
            document.getElementById('alertBox').textContent = data.error;
            document.getElementById('alertBox').classList.add('alert-danger');
            document.getElementById('alertBox').classList.remove('d-none');
        }
        else{
            document.getElementById('alertBox').textContent = data.message;
            document.getElementById('alertBox').classList.add('alert-success');
            document.getElementById('alertBox').classList.remove('d-none');
        }
    })

}
document.addEventListener('DOMContentLoaded',() => loadTransactions('default'));