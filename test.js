var XMLHttpRequest = require("xmlhttprequest").XMLHttpRequest;

function httpPost(url, body, rawPhone) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", url);
    xhr.setRequestHeader("Accept", "application/xml");
    xhr.setRequestHeader("Content-Type", "application/xml");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (!xhr.responseText.includes('<ok/>')) {
                console.log('Error: ' + xhr.responseText + ' for ' + rawPhone)
            }
        } else {
            console.log('xhr.readyState: ' + xhr.readyState + ' for ' + rawPhone)
        }
    };
    xhr.send(body);
}
function sendOne() {
    let rawPhone = '510-798-1123'
    let ph = rawPhone.replace(/\D/g, '')
    if (ph.length !== 10) {
        console.log('Bad phone number: ' + rawPhone)
    } else {
        let caseNumber = '1111111'
        let theDate = new Date()
        let theLoc = 'Location'
        let theRoom = 'Court Date Room' 
        let html = `<?xml version="1.0"?>
<sms>
    <auth_key></auth_key>
    <command>send_message</command>
    <account_id></account_id>
    <short_code></short_code>
    <keyword></keyword>
    <message>You are receiving this email because you have applied for emergency rental assistance \
from the Memphis and Shelby County Emergency Rental Assistance program. \
You have a court eviction hearing on ${theDate} in building ${theLoc}, room ${theRoom}. \
Your case number is ${caseNumber}. \
To verify your court date, call the Court Clerk at (???) ????-???? or \
view your case information at \
https://gscivildata.shelbycountytn.gov/pls/gnweb/ck_public_qry_doct.cp_dktrpt_frames?${caseNumber}. \
Please plan to arrive at court *at least* 15 minutes early to find parking and get to your courtroom. \
This message was sent by an automated system from https://npimemphis.org. Please do not reply. Thank you.</message>
    <contacts>
        <contact_number>+1${ph}</contact_number>
    </contacts>
</sms>`
        httpPost('https://www.txt180.com/members/api.php', html, rawPhone)
    }
}
sendOne()
