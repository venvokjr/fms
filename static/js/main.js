let formerName = null;
let formerPhone = null;

document.getElementById('searchMember').addEventListener('keyup', event => {
    
    var searchValue = event.target.value.toLowerCase(); 
    let rows = document.querySelectorAll('#memberTable tr');

    rows.forEach(row => {
        let name = row.cells[0].textContent.toLowerCase();
        if(name.includes(searchValue)){
            row.style.display = 'table-row';
        }
        else{
            row.style.display = 'none';
        }
    })

})

document.getElementById('BtnMahesabu').addEventListener('click', event => {
    document.getElementById('spiner-mahesabu').style.display = 'block';
    document.getElementById('summaryote').style.display = 'none';
    fetch('/get_summary',{
        method : 'POST',
        headers : { "Content-Type" : "application/json"},
    })
    .then(response => response.json())
    .then(data => {
        if(!data.error){
            setTimeout(()=>{
                document.getElementById('spiner-mahesabu').style.display = 'none';
                document.getElementById('summaryote').style.display = 'block';
            },1000)
            document.getElementById('totalMoney').innerHTML = `Jumla Kuu: <strong style="color: hsl(32, 100%, 50%);">${data.totalCollection.toLocaleString()}</strong> TZS`;
            document.getElementById('totalPaid').innerHTML = `Jumla ya Fedha Taslimu(Ambayo Imeshalipwa): <strong style="color: hsl(32, 100%, 50%);">${data.totalPaid.toLocaleString()}</strong> TZS`;
            document.getElementById('totalDebt').innerHTML = `Jumla ya Ahadi (Ambayo Haijalipwa): <strong style="color: hsl(32, 100%, 50%);">${data.totalDebt.toLocaleString()}</strong> TZS`;
            document.getElementById('totalAdditional').innerHTML = `Jumla ya Ziada(Nyongeza): <strong style="color: hsl(32, 100%, 50%);"> ${data.totalAdditional.toLocaleString()}</strong> TZS`;
            document.getElementById('maelezo').innerHTML =
             `<div><br><u><strong>Ufafanuzi</strong></u><br> 
             Jumla Kuu imepatikana baada ya kujumlisha pesa zote
             zilizolipwa pamoja na madeni(ahadi ambao hazijalipwa) <br> <br> 
            
            Fedha Taslimu ni jumla ya pesa zote zilizotolewa siku ya kwanza kama cash na pesa ambazo mchangiaji ametoa kupunguza ahadi yake <br><br> 
            Jumla ya Ahadi ni jumla ya ahadi zote zilizobaki ambazo bado hazijalipwa tu <br><br> 
            Jumla ya Nyongeza ni pesa zote ambazo mtu alitoa zaidi ya alichoahidi mfano alliahidi 50,0000 akatoa 60,0000 ivyo nyongeza ni 10,0000
              </div>` ;
        }
        else{
            if(data.error){
               document.getElementById('totalError').textContent = data.error
            }
           
        }

    })
   .catch(error => document.getElementById('totalError').textContent = error)

})

function Edit(button){
    const name = button.getAttribute('data-name');
    const phone = button.getAttribute('data-phone');
    document.getElementById('edit-name').value = name;
    document.getElementById('edit-phone').value = phone;
    document.getElementById('jinalake').textContent = name;
    formerName = name.trim();
    formerPhone = phone.trim();
}

function deleteUser(){
    fetch('/delete_user',{
        method: 'POST',
        headers: { "Content-Type": "application/json"},
        body: JSON.stringify({formerName})
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

function commitChange(event){
    event.preventDefault();
    
    const name = (document.getElementById('edit-name').value).trim();
    const phone = (document.getElementById('edit-phone').value).trim();

    if(name === '' || phone === ''){
        document.getElementById('alertBoxUser').textContent = `Tafadhali ingiza taarifa zote kwa usahihi`;
        document.getElementById('alertBoxUser').classList.add('alert-danger');
        document.getElementById('alertBoxUser').classList.remove('d-none');
        return
    }
    else if(phone !== "null" && phone.length !== 10){
        document.getElementById('alertBoxUser').textContent = `Hakikisha namba za simu ulizoweka ni sahihi na zina tarakimu 10`;
        document.getElementById('alertBoxUser').classList.add('alert-danger');
        document.getElementById('alertBoxUser').classList.remove('d-none');
        return
    }

    if(phone !== "null" && !phone.startsWith('0')){
        document.getElementById('alertBoxUser').textContent = `Hakikisha namba za simu ulizoweka inaanza na sifuri(0)`;
        document.getElementById('alertBoxUser').classList.add('alert-danger');
        document.getElementById('alertBoxUser').classList.remove('d-none');
        return
    }
    fetch('/edit_member_info',{
        method : 'POST',
        headers: { "Content-Type": "application/json" },
        body : JSON.stringify({name,phone,formerName,formerPhone})
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        if(data.error){
            document.getElementById('alertBoxUser').textContent = data.error;
            document.getElementById('alertBoxUser').classList.add('alert-danger');
            document.getElementById('alertBoxUser').classList.remove('d-none');
        }
        else{
            document.getElementById('editUserInfo').reset();
            document.getElementById('alertBoxUser').textContent = data.message;
            document.getElementById('alertBoxUser').classList.add('alert-success');
            document.getElementById('alertBoxUser').classList.remove('d-none');
            setTimeout(() => {window.location.reload()},2000)
        }   
    })
    .catch(error => {
        
        document.getElementById('alertBoxUser').textContent = error;
        document.getElementById('alertBoxUser').classList.add('alert-danger');
        document.getElementById('alertBoxUser').classList.remove('d-none');
    })
}

function capitalize(name){
    let yap = name.split(' ');
    let fullname = '';
    yap.forEach(word => {
        let formated = word.charAt(0).toUpperCase() + word.slice(1) + ' ';
        fullname += formated;
    })
    return String(fullname);
    
}

function loadMembers(sortby){
    
    fetch('/get_members',{
        method: 'POST',
        headers: { "Content-Type": "application/json"},
        body: JSON.stringify({sortby})
    })
    .then(response => response.json())
    .then(data =>{
        const users = data.length;
        let table = document.getElementById('memberTable');
        const usersAmount = document.getElementById('userAmount');
        usersAmount.textContent = `Idadi ya wachangiaji: ${users}`
        table.innerHTML = ``;
        data.forEach(member => {
            member.name = capitalize(member.name);
            const row = `
            <tr>
                <td>${member.name}</td>
                <td>${member.phone}</td>
                <td>${member.promise_amount.toLocaleString()}</td>
             <!--   <td>${member.cash_amount.toLocaleString()}</td> -->
                <td>${member.paid_amount.toLocaleString()}</td>
                <td>${member.debt_amount.toLocaleString()}</td>
               <!-- <td>${member.addition_amount.toLocaleString()}</td> -->
                <td style="background-color:hsl(0, 0.00%, 23.10%);">
                    <button
                        data-name= "${member.name}"
                        data-phone = "${member.phone}"
                        data-bs-target="#makeEdits" 
                        data-bs-toggle="modal"  
                        onclick="Edit(this)"
                        style="border: none;color: hsl(140, 59.20%, 39.40%);font-family: sans-serif;background-color: hsl(0, 0.00%, 23.10%);">Fanya Rekebisho
                    </button>
                </td>
            </tr>
            `
            table.innerHTML += row;
        })
        setTimeout(()=>{
            document.getElementById('spiner-body').style.display = 'none';
            document.getElementById('thebody').style.display = 'block';
        },2000);
    });

}

document.addEventListener('DOMContentLoaded',() => loadMembers('default'));
