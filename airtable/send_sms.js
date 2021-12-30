class TextSender {
    httpPost(url, body, rawPhone) {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", url);
        xhr.setRequestHeader("Content-Type", "application/html");
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
    sendOne(rec) {
        let rawPhone = rec.getCellValue('ApplicantMobile')
        let ph = rawPhone.replace(/\D/g, '')
        if (length(ph) !== 10) {
            console.log('Bad phone number: ' + rawPhone)
        } else {
            let caseNumber = rec.getCellValue('Eviction Case Number')
            let theDate = rec.getCellValue('Next Court Date')
            let theLoc = rec.getCellValue('Next Court Date Location')
            let theRoom = rec.getCellValue('Next Court Date Room') 
            let html = `<sms>
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
            this.httpPost('https://www.txt180.com/members/api.php', html, rawPhone)
        }
    }
    send(query) {
        // TODO: Genericize test in notify_client_of_court_date.
        this.sendOne(null)
    }
}
let table = base.getTable('All Applicants')
let query = await table.selectRecordsAsync({fields: table.fields})
new TextSender.send(query)