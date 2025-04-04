function allfunctions(){
    var form = document.getElementById('loginForm') 
    form.addEventListener('submit', (event) =>{
        if(!form.checkValidity()){
            event.preventDefault();
            event.stopPropagation();
        }
        else{
            const recaptchaResponse = grecaptcha.getResponse();
            event.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            document.getElementById('username').disabled=true;
            document.getElementById('password').disabled=true;
            document.querySelector('button').disabled=true;
            document.querySelector('button').textContent = `Loading...`;

            fetch('/verify_credentials',{
                method : "POST",
                headers : {'Content-Type' : 'application/json'},
                body: JSON.stringify({username,password,recaptchaResponse})
            })
            .then(response => response.json())
            .then(data => {
                permission = data.permitted
                denial = data.error
                admin = data.is_admin
                if(permission === true && denial === null){
                    if(!admin){
                        window.location.href = '/dashboard';
                    }
                    else{
                        window.location.href = `/admin/dashboard`;
                    }
                    
                }
                else{
                    document.getElementById('username').disabled=false;
                    document.getElementById('password').disabled=false;
                    document.querySelector('button').disabled=false;
                    document.querySelector('button').textContent = `Login`;
                    document.getElementById('errorAlert').classList.remove('d-none');
                    document.getElementById('errorAlert').textContent = denial;
                }
            })
        }
        form.classList.add('was-validated');
    })
}
function showPassword(){
    let passField = document.getElementById('password');
    if(passField.type === 'password'){
        passField.setAttribute('type','text');
        document.getElementById('eyeIcon').style.display = 'none';
        document.getElementById('eyeIconHide').style.display = 'block';
    }
    else{
        document.getElementById('eyeIcon').style.display = 'block';
        document.getElementById('eyeIconHide').style.display = 'none';
        passField.setAttribute('type','password');
    }
}


document.addEventListener('DOMContentLoaded',allfunctions);

