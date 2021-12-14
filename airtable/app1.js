class App1 {
    buildBody(rec) {
        return `You are receiving this email because you have applied for eviction/rental help from Neighborhood Preservation, Inc.

You have a court eviction hearing on ${rec.getCellValue('Next Court Date')} \
in building ${rec.getCellValue('Next Court Date Location')}, \
room ${rec.getCellValue('Next Court Date Room')}. Your case number is ${rec.getCellValue('Eviction Case Number')}.

You may have received U.S. Postal mail from the court containing a court date and location. That information may be incorrect.

To verify your court date, you can call the Court Clerk at (901) 222-3500. ***What should the phone number be?***. \
You can also view your case information at \
https://gscivildata.shelbycountytn.gov/pls/gnweb/ck_public_qry_doct.cp_dktrpt_frames?case_id=${rec.getCellValue('Eviction Case Number')}.

Please plan to arrive at court *at least* 15 minutes early to find parking and get to your courtroom. ***Any other tips here?***

This message was sent by an automated system from https://npimemphis.org. Please do not reply. Thank you.`
    }
    buildEmail(rec) {
        return `Hello ${rec.getCellValue('AppFirstName')} ${rec.getCellValue('AppLastName')},

${this.buildBody(rec)}`
    }
    showEmail(rec) {
        let msg = `To: ${rec.getCellValue('ApplicantEmail')}
From: do-not-reply@npimemphis.org
Subject: Your court eviction hearing

${this.buildEmail(rec)}`
        console.log(msg)
    }
    runIt(query) {
        let alreadyMarkedRecords = query.records.filter(rec => {
            return (rec.getCellValue('Email For Automation'))
        })
        for (let rec of alreadyMarkedRecords) {
            table.updateRecordAsync(rec, {'Email For Automation' : ''})
        }
        let filteredRecords = query.records.filter(rec => {
            let caseNumber = rec.getCellValue('Eviction Case Number')
            let status = rec.getCellValue('Case Status (In Neighborly)')
            let status_val = ''
            if (status && status[0] && status[0]['name']) {
                status_val = status[0]['name']
            }
            return (status_val.includes('Approved: Sent for legal') &&
                    caseNumber !== 'Not Found' &&
                    caseNumber !== '' &&
                   !rec.getCellValue('Tenant Case Email Sent') &&
                    rec.getCellValue('ApplicantEmail') &&                   
                    rec.getCellValue('Next Court Date') &&            
                    rec.getCellValue('Next Court Date Location') &&
                    rec.getCellValue('Next Court Date Room') 
                   )
        })
        let c = 0
        for (let rec of filteredRecords) {
            let now = new Date()
            let email = rec.getCellValue('ApplicantEmail')
            table.updateRecordAsync(rec, {'Email For Automation' : email})
            table.updateRecordAsync(rec, {'Tenant Case Email Sent' : now})
            c++
        }
        console.log('Marked ' + c + ' applicants for automated email sending.');
    }
}
let table = base.getTable('All Applicants');
let query = await table.selectRecordsAsync({fields: table.fields});
new App1().runIt(query);