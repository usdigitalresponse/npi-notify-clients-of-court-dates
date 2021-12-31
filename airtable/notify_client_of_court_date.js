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
            let now = new Date()
            table.updateRecordAsync(rec, {'Tenant Case SMS Sent' : now})
        }
    }
}

class App1 {
    async setItUp(query) {
        let alreadyMarkedRecords = query.records.filter(rec => {
            return (rec.getCellValue('Email For Automation'))
        })
        let c1 = 0
        for (let rec of alreadyMarkedRecords) {
            table.updateRecordAsync(rec, {'Email For Automation' : ''})
            c1++
        }
        console.log(c1 + ' Email For Automation value(s) cleared')
    }
    async triggerEmail(rec) {
        let now = new Date()
        let email = rec.getCellValue('ApplicantEmail')
        table.updateRecordAsync(rec, {'Email For Automation' : email})
        table.updateRecordAsync(rec, {'Tenant Case Email Triggered' : now})
    }
    async sendSMS(rec) {
        let ts = new TextSender()
        await ts.sendOne(rec)
    }
    async runIt(query, emailOrPhoneColumn) {
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
            if (emailOrPhoneColumn === 'ApplicantEmail') {
                sentStatusColName = 'Tenant Case Email Triggered'
            } else {
                sentStatusColName = 'Tenant Case SMS Sent'
            }
            let canSend = !rec.getCellValue(sentStatusColName) &&
                       rec.getCellValue(emailOrPhoneColumn)
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
            if (emailOrPhoneColumn === 'ApplicantEmail') {
                await this.triggerEmail(rec)
            } else {
                await this.sendSMS(rec)
            }
            c++
        }
        if (emailOrPhoneColumn === 'ApplicantEmail') {
            console.log('Marked ' + c + ' applicant(s) for automated email sending.')
        } else {
            console.log('Sent text messages to ' + c + ' applicant(s).')
        }
    }
    async triggerEmails(query) {
        await app.setItUp(query)
        await app.runIt(query, 'ApplicantEmail')
    }
}
let table = base.getTable('All Applicants');
let query = await table.selectRecordsAsync({fields: table.fields});
let app = new App1()
await app.triggerEmails(query)
// await app.runIt('ApplicantMobile')