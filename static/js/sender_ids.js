// Mock data - Replace with actual API calls
let all_usernames = []
const mockUsers = [
    { 
        username: "user1", 
        sender_ids: ["FMSPOINT", "DONATE"] 
    },
    { 
        username: "user2", 
        sender_ids: ["FUNDRAISE"] 
    },
    { 
        username: "user3", 
        sender_ids: ["CHANGO", "DONATE", "FUNDS"] 
    }
];

// DOM Elements
const senderIdsTableBody = document.getElementById('senderIdsTableBody');
const globalSenderIdInput = document.getElementById('globalSenderId');
const addGlobalSenderBtn = document.getElementById('addGlobalSenderBtn');

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    loadSenderIds();
    setupEventListeners();
});

function loadSenderIds() {
    all_usernames = []
    fetch('/admin/get_senderids',{
        method: 'GET',
        headers: {'Content-Type': 'application/json'},
    })
    .then(res => res.json())
    .then(data => {
        data.forEach(user =>{
            all_usernames.push(user.username);
        })
        senderIdsTableBody.innerHTML = data.map(user => `
            <tr>
                <td>${user.username}</td>
                <td>
                    <div class="d-flex flex-wrap">
                        ${user.sender_ids.map(sender => `
                            <span class="badge sender-id-badge">
                                ${sender}
                                <i class="bi bi-x-circle remove-sender" 
                                   data-sender="${sender}" 
                                   data-user="${user.username}"></i>
                            </span>
                        `).join('')}
                    </div>
                </td>
                <td>
                    <div class="input-group">
                        <input type="text" 
                               class="form-control user-sender-input" 
                               placeholder="New Sender ID" 
                               data-user="${user.username}">
                        <button class="btn btn-outline-primary add-user-sender" 
                                data-user="${user.username}">
                            <i class="bi bi-plus"></i> Add
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    })
    
}

function setupEventListeners() {
    // Add sender ID to all users
    addGlobalSenderBtn.addEventListener('click', function() {
        const senderId = globalSenderIdInput.value.trim();
        if (senderId) {
            if (confirm(`Add "${senderId}" to ALL users?`)) {

                fetch('/admin/global_sender_id_add',{
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({all_usernames,senderId})
                })
                .then(res => res.json())
                .then(data => {
                    let suc = data.success;
                    let fail = data.error;
                    if(fail){
                        alert(`It worked for the rest except the folling ${fail}`)
                    }
                    else{
                        alert(`Sender IDS have been added successfully`)
                    }
                    
                    globalSenderIdInput.value = ''; 
                    loadSenderIds();
                })

            }
        } else {
            alert('Please enter a Sender ID');
        }
    });

    // Add sender ID to specific user
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('add-user-sender')) {
            const username = e.target.dataset.user;
            const input = e.target.previousElementSibling;
            const senderId = input.value.trim();
            const action = 'add';
            if (senderId) {
                // API call would go here
                fetch('/admin/single_sender_id_add',{
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({username,senderId,action})
                })
                .then(res => res.json())
                .then(data => {
                    if(data.message){
                        alert(data.message)
                    }
                    else{
                        alert(data.error)
                    }
                    
                    globalSenderIdInput.value = ''; 
                    loadSenderIds();
                })
            } else {
                alert('Please enter a Sender ID');
            }
        }
    });

    // Remove sender ID from user
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-sender')) {
            const senderId = e.target.dataset.sender;
            const username = e.target.dataset.user;
            
            if (confirm(`Remove "${senderId}" from ${username}?`)) {
                const action = 'remove';
                if (senderId) {
                    fetch('/admin/single_sender_id_add',{
                        method: 'POST',
                        headers: {'Content-Type':'application/json'},
                        body: JSON.stringify({username,senderId,action})
                    })
                    .then(res => res.json())
                    .then(data => {
                        if(data.message){
                            alert(data.message)
                        }
                        else{
                            alert(data.error)
                        }
                        
                        globalSenderIdInput.value = ''; 
                        loadSenderIds();
                    })
                }    
            }
        }
    });
}

// Helper function for API calls (replace with actual fetch)
async function updateSenderIds(user, senderIds) {
    console.log(`Updating ${user} with sender IDs: ${senderIds.join(', ')}`);
    // await fetch(`/api/users/${user}/sender-ids`, {
    //     method: 'POST',
    //     body: JSON.stringify({ sender_ids: senderIds }),
    //     headers: { 'Content-Type': 'application/json' }
    // });
}