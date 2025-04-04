// DOM Elements
const dbUserSelect = document.getElementById('dbUserSelect')
const userTableBody = document.getElementById('userTableBody');
const senderTableBody = document.getElementById('senderTableBody');
const blockTableBody = document.getElementById('blockTableBody');
const licenseTableBody = document.getElementById('licenseTableBody');
const lastUpdatedEl = document.getElementById('lastUpdated');
const alertColor = document.getElementById('toastAlert');

// Initialize the admin panel
document.addEventListener('DOMContentLoaded', function() {
    // Set last updated time
    document.getElementById('spiner-body').style.display = 'block';
    document.getElementById('therest').style.display = 'none';
    lastUpdatedEl.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;

    
    // Load all data
    loadAll();
    loadLicenses();
    
    // Set up event listeners
    setupEventListeners();
});

function loadAll() {
    fetch('/admin/get_users', {
        method: 'GET',
        headers: {'Content-Type': 'application/json'},
    })
    .then(res => res.json())
    .then(data => {
        the_users = data[1];
        balance_info = data[0]

        document.getElementById("totalSMS").textContent = `${balance_info.total_rem}`;
        document.getElementById("usedSMS").textContent = `${balance_info.bought_sms}`;
        document.getElementById("unusedSMS").textContent = `${balance_info.unbought_balance}`;
        
        dbUserSelect.innerHTML = data[1].map(user=> `
            <option value="${user.username}">${user.username}<option>`);
        userTableBody.innerHTML = data[1].map(user => `
            <tr>
                <td>${user.username}</td>
                <td>${user.fullname}</td>
                <td>
                    <span class="balance-view">${user.sms_balance}</span>
                    <input type="number" class="balance-edit form-control edit-balance-input d-none" 
                           value="${user.sms_balance}" data-username="${user.username}">
                </td>
                <td>
                    <span class="badge badge-status ${user.status === false ? 'badge-active' : 'badge-blocked'}">
                        ${user.status === false ? 'Active' : 'Blocked'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary edit-balance-btn" data-username="${user.username}">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-outline-success save-balance-btn d-none" data-username="${user.username}">
                        <i class="bi bi-check"></i> Save
                    </button>
                </td>
            </tr>
        `).join('');
        
        // Update block table using the same data
        blockTableBody.innerHTML = data[1].map(user => `
            <tr>
                <td>${user.username}</td>
                <td>
                    <div class="form-check form-switch">
                        <input class="form-check-input user-status-toggle" type="checkbox" 
                               id="toggle-${user.username}" ${user.status === false ? 'checked' : ''}
                               data-username="${user.username}">
                        <label class="form-check-label" for="toggle-${user.username}">
                            ${user.status === false ? 'Active' : 'Blocked'}
                        </label>
                    </div>
                </td>
                <td>${user.lastActive || 'N/A'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-secondary view-user-btn" data-username="${user.username}">
                        <i class="bi bi-eye"></i> View
                    </button>
                </td>
            </tr>
        `).join('');
    })
    .catch(error => console.error('Error:', error));
    document.getElementById('spiner-body').style.display = 'none';
    document.getElementById('therest').style.display = 'block';
}

// Declare the_users globally
let the_users = [];


function loadLicenses() {
    fetch('/admin/get_licenses',{
        method: 'GET',
        headers: {'Content-Type':'application/json'}
    })
    .then(res => res.json())
    .then(data => {
        licenseTableBody.innerHTML = data.map(license => `
            <tr>
                <td>${license.license_key}</td>
                <td>
                    <span class="badge ${license.status === 'used' ? 'bg-success' : 
                                        license.status === 'unused' ? 'bg-secondary' : 'bg-danger'}">
                        ${license.status.charAt(0).toUpperCase() + license.status.slice(1)}
                    </span>
                </td>
                <td>${license.usedBy || 'N/A'}</td>
                <td>
                    ${license.status === 'unused' ? `
                    <button class="btn btn-sm btn-outline-danger revoke-license-btn" data-code="${license.license_key}">
                        <i class="bi bi-x-circle"></i> Revoke
                    </button>` : ''}
                </td>
            </tr>
        `).join('');
    })
}

function setupEventListeners() {
    // Balance editing
    document.addEventListener('click', function(e) {
        if (e.target.closest('.edit-balance-btn')) {
            const username = e.target.closest('.edit-balance-btn').dataset.username;
            const row = e.target.closest('tr');
            row.querySelector('.balance-view').classList.add('d-none');
            row.querySelector('.balance-edit').classList.remove('d-none');
            row.querySelector('.edit-balance-btn').classList.add('d-none');
            row.querySelector('.save-balance-btn').classList.remove('d-none');
        }
        
        if (e.target.closest('.save-balance-btn')) {
            const username = e.target.closest('.save-balance-btn').dataset.username;
            const row = e.target.closest('tr');
            const newBalance = row.querySelector('.balance-edit').value;
            
            
            fetch('/admin/edit_user_balance',{
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({username,newBalance})
            })
            .then(res => res.json())
            .then(data => {
                
                if(!data.error){
                    row.querySelector('.balance-view').textContent = newBalance;
                    row.querySelector('.balance-view').classList.remove('d-none');
                    row.querySelector('.balance-edit').classList.add('d-none');
                    row.querySelector('.edit-balance-btn').classList.remove('d-none');
                    row.querySelector('.save-balance-btn').classList.add('d-none');
                    
    
                    showToast(`Successfully updated ${username}'s SMS balance to ${newBalance}`);

                }
                else{
                    alertColor.classList.remove('bg-success');
                    alertColor.classList.add('bg-danger');
                    showToast(` ${data.error}`);
                }
            })
            .catch(error=>{
                alertColor.classList.remove('bg-success');
                alertColor.classList.add('bg-danger');
                showToast(error);
            })
        }
    });
    
    // User blocking toggle
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('user-status-toggle')) {
            const username = e.target.dataset.username;
            let isBlocked = null;
            if(e.target.checked){
                isBlocked = false
            }
            else{
                isBlocked= true;
            }
            
            fetch('/admin/block_user',{
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({username,isBlocked})
            })
            .then(res => res.json())
            .then(data => {
                if(data.error){
                    alertColor.classList.remove('bg-success');
                    alertColor.classList.add('bg-danger');
                    showToast(`${isBlocked ? 'blocked' : 'unblocked'} user ${username} is unsuccessfully❌❌`);
                }
                else{
                    const label = e.target.nextElementSibling;
                    label.textContent = isBlocked ? 'Blocked' : 'Active';
                    showToast(`Successfully ${isBlocked ? 'blocked' : 'unblocked'} user ${username}`);
                }
            })
 
            
        }
    });
    
    // Generate licenses
    document.getElementById('generateLicenseBtn').addEventListener('click', function() {
        const quantity = parseInt(document.getElementById('licenseQuantity').value) || 1;
        
        fetch('/admin/gen_license',{
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({quantity})
        })
        .then(res => res.json())
        .then(data=>{
            if(data.message){
                showToast(data.message);
                window.location.reload();
            }
        })
    });
    
    // Revoke license
    document.addEventListener('click', function(e) {
        if (e.target.closest('.revoke-license-btn')) {
            const code = e.target.closest('.revoke-license-btn').dataset.code;
            if (confirm(`Are you sure you want to revoke license ${code}?`)) {
                // Here you would make an API call to revoke the license
                
                fetch('/admin/revoke_license',{
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({code})
                })
                .then(res => res.json())
                .then(data=>{
                    if(data.message){
                        showToast(data.message);
                        window.location.reload();
                    }
                    else{
                        alertColor.classList.remove('bg-success');
                        alertColor.classList.add('bg-danger');
                        showToast(data.error);
                    }
                })
            }
        }
    });
    
    // Database tools
    document.getElementById('exportCollectionBtn').addEventListener('click', function() {
        const user = document.getElementById('dbUserSelect').value;
        const collection = document.getElementById('dbCollectionSelect').value;
        
        if (!user || !collection) {
            showToast('Please select both a user and collection');
            return;
        }

        fetch('/admin/export_db', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user, collection})
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.blob(); // Convert response to Blob
        })
        .then(blob => {
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Generate filename from current date/time
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            a.download = `${user}-${collection}-${timestamp}.json`;
            
            document.body.appendChild(a);
            a.click();
            
            // Clean up
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => {
            console.error('Error exporting collection:', error);
            alertColor.classList.remove('bg-success');
            alertColor.classList.add('bg-danger');
            showToast('Failed to export collection: ' + error.message);
        });
    });

    document.getElementById('importCollectionBtn').addEventListener('click', function() {
        document.getElementById('collectionImportFile').click();
    }); 
    
    document.getElementById('collectionImportFile').addEventListener('change', function(e) {
        const file = e.target.files[0];
        const errorElement = document.getElementById('importError');
        errorElement.textContent = '';
        
        // 1. Basic validation
        if (!file) return;
        
        // 2. File type validation
        if (!file.name.endsWith('.json')) {
            errorElement.textContent = 'Only JSON files are allowed';
            return;
        }
        
        // 3. File size limit (e.g., 5MB)
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            errorElement.textContent = 'File size exceeds 5MB limit';
            return;
        }
        
        // 4. Read and validate JSON content
        const reader = new FileReader();
        
        reader.onload = function(e) {
            try {
                // 5. Parse JSON with validation
                const data = JSON.parse(e.target.result);
                
                // 7. If everything is valid, proceed with import
                importValidatedData(data);
                
            } catch (error) {
                errorElement.textContent = `Invalid JSON: ${error.message}`;
                console.error('JSON parse error:', error);
            }
        };
        
        reader.onerror = function() {
            errorElement.textContent = 'Error reading file';
        };
        
        reader.readAsText(file);
    });
    
    function importValidatedData(data) {
        // Get user and collection from your UI
        const user = document.getElementById('dbUserSelect').value;
        const collection = document.getElementById('dbCollectionSelect').value;
        
        if (!user || !collection) {
            alertColor.classList.remove('bg-success');
            alertColor.classList.add('bg-danger');
            showToast('Please select both user and collection');
            return;
        }
        
        // Send to backend
        fetch('/admin/import_db', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user,
                collection,
                data
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Import failed');
            return response.json();
        })
        .then(result => {
            showToast(`Successfully imported document`);
            // Refresh your UI if needed
        })
        .catch(error => {
            console.error('Import error:', error);
            alertColor.classList.remove('bg-success');
            alertColor.classList.add('bg-danger');
            showToast('Import failed: ' + error.message);
        });
    }

}

// Helper function to simulate API calls (replace with actual fetch calls)
async function fetchData(endpoint) {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // In a real implementation, you would use:
    // return fetch(`/admin_api/${endpoint}`).then(res => res.json());
    
    // Mock responses
    switch(endpoint) {
        case 'users':
            return mockUsers;
        case 'senders':
            return mockSenders;
        case 'licenses':
            return mockLicenses;
        default:
            return [];
    }
}

function showToast(message) {
    document.getElementById('toastAlertMessage').innerText = message;
    let toast = new bootstrap.Toast(document.getElementById('toastAlert'));
    toast.show();
}

