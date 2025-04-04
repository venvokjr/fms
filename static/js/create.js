let contacts = 1;

document.addEventListener('DOMContentLoaded',()=>{
    (function () {
        'use strict';
        var forms = document.querySelectorAll('.needs-validation');
        Array.prototype.slice.call(forms).forEach(function (form) {
            form.addEventListener('submit', function (event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    })();
});

function removeContact(button){
    button.parentElement.remove();
    contacts -= 1;
}

function addContact(){
    const ContactList = document.getElementById('contactList');
    const newContact = document.createElement('div');
    newContact.className = 'contact-entry';
    newContact.innerHTML = `
        <input type="text" class="form-control" id="cntname${contacts+1}" placeholder="Contact Name" required>
        <input type="text" class="form-control" id="cntnumber${contacts+1}" placeholder="Contact Number" required>
        <button type="button" class="btn btn-danger btn-sm" onclick="removeContact(this)">X</button>
    `
    ContactList.appendChild(newContact);
    contacts += 1;
}

document.getElementById('registerForm').addEventListener('submit',(event)=>{
    event.preventDefault();
    const FullName = document.getElementById('fullname').value;
    const username = document.getElementById('username').value;
    const password1 = document.getElementById('password').value;
    const password2 = document.getElementById('confirmPassword').value;
    const email = document.getElementById('email').value;
    const license = document.getElementById('license').value;


    if(!FullName || !username || !password1|| !password2|| !email || !license){
        alertBox.textContent = `Tafadhali hakikisha unajaza taarifa zote`;
        alertBox.classList.add('alert-danger');
        alertBox.classList.remove('d-none');
        return
    }


    if(password1!==password2){
        alertBox.textContent = `Tafadhali hakikisha unaweka password zinazofanana`;
        alertBox.classList.add('alert-danger');
        alertBox.classList.remove('d-none');
        return
    }

   // console.log(FullName,username,email,password2,ocassion,contact_names,contact_numbers,license);
    disabler(true);
    const recaptchaResponse = grecaptcha.getResponse();
    fetch('/register_user', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({FullName,username,email,password2,license,recaptchaResponse})
    })
    .then(response => response.json())
    .then((data) => {
        disabler(false);
        if(data.error){
            alertBox.textContent = `${data.error}`;
            alertBox.classList.add('alert-danger');
            alertBox.classList.remove('d-none');
        }
        else if(data.permit){
            window.location.method = 'GET';
            window.location.href = '/verifier';
        }
    })
    .catch((error) => {
        disabler(false);
        alertBox.textContent = `${error}`;
        alertBox.classList.add('alert-danger');
        alertBox.classList.remove('d-none');
    })

})

function disabler(bool){
    const FullName = document.getElementById('fullname');
    const username = document.getElementById('username');
    const password1 = document.getElementById('password');
    const password2 = document.getElementById('confirmPassword');
    const email = document.getElementById('email');
    const license = document.getElementById('license');
    const regButton = document.getElementById('register');

    FullName.disabled = username.disabled = password1.disabled= password2.disabled = email.disabled = license.disabled = regButton.disabled = bool;
}