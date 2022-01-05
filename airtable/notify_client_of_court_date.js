class TextSender {
    async sendOne(rec) {
        let rawPhone = rec.getCellValue('ApplicantMobile')
        let ph = rawPhone.replace(/\D/g, '')
        if (ph.length !== 10) {
            console.log('Bad phone number: ' + rawPhone)
        } else {
            let caseNumber = rec.getCellValue('Eviction Case Number')
            let theDate = rec.getCellValue('Next Court Date')
            let theLoc = rec.getCellValue('Next Court Date Location')
            let theRoom = rec.getCellValue('Next Court Date Room') 
            let xml = `<?xml version="1.0"?>
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
            let response = await fetch('https://www.txt180.com/members/api.php', {method: 'POST', body: xml});
            let ret = await response.text();
            if (!ret.includes('<ok/>')) {
                console.log('Error: ' + ret + ' for ' + rawPhone)
            } else {
                let now = new Date()
                table.updateRecordAsync(rec, {'Tenant Case SMS Sent' : now})
            }
        }
    }
}

class App1 {
    async sendSMS(rec) {
        let ts = new TextSender()
        await ts.sendOne(rec)
    }
    async runIt(query) {
        let filteredRecords = query.records.filter(rec => {
            let caseNumber = rec.getCellValue('Eviction Case Number')
            let status = rec.getCellValue('Case Status (In Neighborly)')
            let status_val = ''
            if (status && status[0] && status[0]['name']) {
                status_val = status[0]['name']
            }
            let judge = rec.getCellValue('Next Court Date Judge')
            if (!judge || judge === 'unassigned') {
                judge = ''
            }
            let sentStatusColName;
            sentStatusColName = 'Tenant Case SMS Sent'
            let canSend = !rec.getCellValue(sentStatusColName)
            return (status_val.includes('Approved: Sent for legal') &&
                    caseNumber !== 'Not Found' &&
                    caseNumber !== '' &&
                    canSend &&
                    rec.getCellValue('Next Court Date') &&
                    rec.getCellValue('Next Court Date Location') &&
                    rec.getCellValue('Next Court Date Room') &&
                    judge !== ''
                   )
        })
        let c = 0
        for (let rec of filteredRecords) {
            await this.sendSMS(rec)
            c++
        }
        console.log('Sent text messages to ' + c + ' applicant(s).')
    }
}
let table = base.getTable('All Applicants');
let query = await table.selectRecordsAsync({fields: table.fields});
let app = new App1()
await app.runIt(query)