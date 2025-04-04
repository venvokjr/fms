const badoAnadaiwa = document.getElementById('bado_anadaiwa');
const amelipa_yote = document.getElementById('amelipa_yote');
const fedha_taslimu = document.getElementById('fedha_taslimu');
const ahadi_tu = document.getElementById('ahadi_tu');
const fedha_na_ahadi = document.getElementById('fedha_na_ahadi');
const KumbushaDeni = document.getElementById('kumbusha_deni');

document.addEventListener('DOMContentLoaded',()=>{
    fetch('get_default_template',{
        method: 'GET',
        headers: {'Content-Type': "application/json"},
    })
    .then(response => response.json())
    .then(data => {
        badoAnadaiwa.value = `${data.bado_anadaiwa}`;
        amelipa_yote.value = `${data.amelipa_yote}`;
        fedha_taslimu.value = `${data.fedha_taslimu}`;
        ahadi_tu.value = `${data.ahadi_tu}`;
        fedha_na_ahadi.value = `${data.fedha_na_ahadi}`;
        KumbushaDeni.value = `${data.kumbusha_deni}`;
    })
});

const accepted_placeholders = [
    "{name}", "{payment_type}", "{amount:,}", "{person}",
    "{cash:,}", "{ahadi:,}", "{total:,}","{amount_paid:,}","{amount_debt:,}" , "{debt_amount:,}"
];

function extractPlaceholders(text) {
    const matches = text.match(/{[^}]+}/g); // Find all `{}` placeholders
    return matches ? matches : []; // Return array or empty array
}

templateForm.addEventListener('submit', event => {
    event.preventDefault();

    const badoAnadaiwa = document.getElementById('bado_anadaiwa').value;
    const amelipaYote = document.getElementById('amelipa_yote').value;
    const fedhaTaslimu = document.getElementById('fedha_taslimu').value;
    const ahadiTu = document.getElementById('ahadi_tu').value;
    const fedhaNaAhadi = document.getElementById('fedha_na_ahadi').value;
    const KumbushaDeni = document.getElementById('kumbusha_deni').value;

    
    if (!badoAnadaiwa || !amelipaYote || !fedhaTaslimu || !ahadiTu || !fedhaNaAhadi || KumbushaDeni) {
        alert("⚠️ Tafadhali jaza sehemu zote!");
        return;
    }


    const allTemplates = [badoAnadaiwa, amelipaYote, fedhaTaslimu, ahadiTu, fedhaNaAhadi, KumbushaDeni];

    for (const template of allTemplates) {
        const placeholders = extractPlaceholders(template);
        for (const placeholder of placeholders) {
            if (!accepted_placeholders.includes(placeholder)) {
                alert(`⚠️ Kosa: Kishika nafasi "${placeholder}" hairuhusiwi!`);
                return;
            }
        }
    }

    fetch('/modify_template_message',{
        method: 'POST',
        headers: {"Content-Type": 'application/json'},
        body: JSON.stringify({badoAnadaiwa,amelipaYote,ahadiTu,fedhaTaslimu,fedhaNaAhadi,KumbushaDeni})
    })
    .then(response => response.json())
    .then(data => {
        if(!data.error){
            window.location.reload();
            alert(data.message);
        }
        else{
            alert(data.error);
        }
    })
    .catch(error =>{
        alert(error);
    })
});



