document.addEventListener('DOMContentLoaded', function() {
   
    document.getElementById('loadingIndicator').style.display = 'block';

    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    fetch('/get_sms_balance',{
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
    })
    .then(res => res.json())
    .then(statsData => {
        document.getElementById('balance').textContent = statsData.balance.toLocaleString();
        document.getElementById('sent-sms').textContent = statsData.sent_sms_count.toLocaleString();
        document.getElementById('delivered-sms').textContent = statsData.delivered_sms_count.toLocaleString();
    })
        
    fetch('/get_sms_history',{
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
    })
    .then(res => res.json())
    .then(data => {
        renderSMSCards(data);
    })

    
    
    // Render SMS cards
    function renderSMSCards(data) {
        const container = document.getElementById('smsContainer');
        const template = document.getElementById('smsCardTemplate');
        
        data.forEach(sms => {
            const card = template.content.cloneNode(true);
            
            card.querySelector('.receiver-name').textContent = sms.receiver_name;
            card.querySelector('.receiver-phone').textContent = sms.receiver_phone;
            card.querySelector('.message-content').textContent = sms.message;
            card.querySelector('.sms-count').textContent = sms.sms_count + ' SMS';
            card.querySelector('.send-date').textContent = sms.date;
            card.querySelector('.send-time').textContent = sms.time;
            card.querySelector('.message-id').textContent = 'ID: ' + sms.messageId;
            
            container.appendChild(card);
        });
        setTimeout(()=>{
            document.getElementById('loadingIndicator').style.display = 'none';
        },1500)
        
    }
    
    // Search functionality
    document.getElementById('searchSMS').addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const cards = document.querySelectorAll('.sms-card');
        
        cards.forEach(card => {
            const text = card.textContent.toLowerCase();
            card.style.display = text.includes(searchTerm) ? 'block' : 'none';
        });
    });
    
    /* Filter buttons
    document.querySelectorAll('.filter-buttons .btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.filter-buttons .btn').forEach(b => {
                b.classList.remove('active');
            });
            this.classList.add('active');
            
            // Implement actual filtering logic here
            // This is just a placeholder
        });
    });
    */
});
