document.addEventListener('DOMContentLoaded', event => {
    
    const TableData = document.getElementById('memberTable');
    const SenderIDS = document.getElementById('senderIdTable');
    const selectAllCheckbox = document.getElementById('selectAll');

    fetch('/get_debts', {
        method: "GET",
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        TableData.innerHTML = ''; 
        data.forEach(member => {
            const row = `
            <tr style="color: white;">
                <td>
                <input
                    data-name = "${member.name}"
                    data-phone = "${member.phone}"
                    data-debt = "${member.debt_amount}"
                    type="checkbox"
                ></td>
                <td>${member.name}</td>
                <td>${member.phone}</td>
                <td>${member.debt_amount}</td>
            </tr>    
            `;
            TableData.innerHTML += row;
        });

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

        const memberCheckboxes = document.querySelectorAll('#memberTable input[type="checkbox"]');

        selectAllCheckbox.addEventListener('change', function () {
            memberCheckboxes.forEach((checkbox) => {
                checkbox.checked = selectAllCheckbox.checked;
            });
        });
        setTimeout(()=>{
            var myModal = new bootstrap.Modal(document.getElementById('smsModal'));
            myModal.show();
            document.getElementById('spiner-body').style.display = 'none';
            document.getElementById('thebody').style.display = 'block';
        },100);
    })
    .catch(error => {
        alert(error);
    });
});

document.getElementById('sendSMS').addEventListener('click', ()=>{
    document.getElementById('sendSMS').disabled = true;
    const SenderId = document.getElementById('senderIdTable');
    const memberCheckboxes = document.querySelectorAll('#memberTable input[type="checkbox"]');
    ToBeNotified = []
    memberCheckboxes.forEach(checkbox => {
        checkbox.disabled = true;
        if(checkbox.checked){
            object = {
                "name": checkbox.getAttribute("data-name"),
                "phone": checkbox.getAttribute("data-phone"),
                "debt": checkbox.getAttribute('data-debt')
            }
            ToBeNotified.push(object);
        }
    })

    if (ToBeNotified.length < 1){
        memberCheckboxes.forEach(checkbox  => {
            checkbox.disabled = false;
        })
        document.getElementById('sendSMS').disabled = false;
        return alert('Ni lazima umchague angalau mtu mmoja wa kutumiwa ujumbe')

    }

    packet = [ToBeNotified,SenderId.value]
    //console.log(ToBeNotified);
    fetch('/remind_debts',{
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(packet)
    })
    .then(response => response.json())
    .then(data => {
        memberCheckboxes.forEach(checkbox =>{
            checkbox.disabled = false;
        })
        document.getElementById('sendSMS').disabled = false;
        if(data.results){
            alert("Message were sent successfully");
        }
        else if(data.insufficient){
            alert(data.insufficient);
        }
        else{
            alert("Message was not sent successfully");
        }
    })
})

document.getElementById('searchMember').addEventListener('keyup',(event)=>{

    let searchValue = event.target.value.toLowerCase();
    const rows = document.querySelectorAll('#memberTable tr');

    rows.forEach((row)=>{
        let name = row.cells[1].textContent.toLowerCase();
        if(name.includes(searchValue)){
            row.style.display = 'table-row';
        }
        else{
            row.style.display = 'none';
        }
    })
})