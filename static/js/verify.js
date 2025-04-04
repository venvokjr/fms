
function resendCode(){
    fetch('/resendcodes',{
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
    })
    .then(res => res.json())
    .then(data => {
        if(data.message){
            document.getElementById('alertBox').textContent = data.message ;
            document.getElementById('alertBox').classList.add('alert-success');
            document.getElementById('alertBox').classList.remove('d-none');
        }
        else{
            document.getElementById('alertBox').textContent = data.error ;
            document.getElementById('alertBox').classList.add('alert-danger');
            document.getElementById('alertBox').classList.remove('d-none');
        }
    })
    .catch(error => {
        document.getElementById('alertBox').textContent = error ;
        document.getElementById('alertBox').classList.add('alert-danger');
        document.getElementById('alertBox').classList.remove('d-none');
    })
}

function Verify (){
    const code = document.getElementById('code').value;
    //console.log(code.length);
    if (code.length !== 6){
        document.getElementById('alertBox').textContent = "You must enter 6 digits code before you continue with verification" ;
        document.getElementById('alertBox').classList.add('alert-danger');
        document.getElementById('alertBox').classList.remove('d-none');
        return 
    }

    document.getElementById('code').disabled = true;
    fetch('/verifycodes',{
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({code})
    })
    .then(response => {
        if (!response.ok) throw new Error('Server error: ' + response.status);
        return response.json();
    })
    .then(data => {
        if(data.message){
            document.body.style.backgroundColor = `rgba(0, 0, 0, 0.7)`;
            alert('Account created succesfully');
            window.location.href = '/login';
            
        }
        else{
            document.getElementById('code').disabled = false;
            document.getElementById('alertBox').textContent = data.error;
            document.getElementById('alertBox').classList.add('alert-danger');
            document.getElementById('alertBox').classList.remove('d-none');
        }
    })
    .catch(error=>{
        document.getElementById('code').disabled = false;
        document.getElementById('alertBox').classList.add('alert-primary');
        document.getElementById('alertBox').textContent = error;
        document.getElementById('alertBox').classList.remove('d-none');
    })
}

document.addEventListener('DOMContentLoaded', () => {
    const parent = document.querySelector('.verify-container'); // Fix the selector
    const resend = document.createElement('div');
    resend.classList.add('resend'); // Add class for styling
    parent.appendChild(resend); // Append before setting interval

    let rem_time = 60; // Countdown time

    function updateResendText() {
        if (rem_time > 0) {
            resend.innerHTML = `Didn't receive the code? <span style="color:gray;">Resend in ${rem_time} s</span>`;
        } else {
            resend.innerHTML = `Didn't receive the code? <span onclick="resendCode()" style="cursor:pointer;color:blue;">Resend</span>`;
        }
    }

    // Run every second
    const timer = setInterval(() => {
        rem_time--;
        updateResendText();

        if (rem_time <= 0) {
            clearInterval(timer); // Stop the timer when time reaches 0
        }
    }, 1000);

    updateResendText(); // Initial render
});

function createBalloons() {
    for (let i = 0; i < 10; i++) {
        let balloon = document.createElement("div");
        balloon.className = "balloon";
        balloon.style.left = Math.random() * 100 + "vw";
        balloon.style.background = `hsl(${Math.random() * 360}, 100%, 50%)`;
        document.body.appendChild(balloon);
        setTimeout(() => balloon.remove(), 5000);
    }
}
function createFireworks() {
    for (let i = 0; i < 20; i++) {
        let firework = document.createElement("div");
        firework.className = "firework";
        firework.style.left = Math.random() * 100 + "vw";
        firework.style.top = Math.random() * 100 + "vh";
        document.body.appendChild(firework);
        setTimeout(() => firework.remove(), 1000);
    }
}


