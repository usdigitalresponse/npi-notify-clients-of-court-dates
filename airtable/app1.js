class App1 {
    buildBody(rec) {
        return `You are receiving this email because you have applied for eviction/rental help from Neighborhood Preservation, Inc.

You have a court eviction hearing on ${rec.getCellValue('Next Court Date')} 
at building: ${rec.getCellValue('Next Court Date Location')}, 
in room" ${rec.getCellValue('Next Court Date Room')}. Your case number is ${rec.getCellValue('Eviction Case Number')}.

You may have received U.S. Postal mail from the court containing a court date and location. That information may be incorrect. 
To verify your court date, you can call the Court Clerk at (901) 222-3500. <b>What should the phone number be?</b>. 
You can also view your case information at 
https://gscivildata.shelbycountytn.gov/pls/gnweb/ck_public_qry_doct.cp_dktrpt_frames?case_id=${rec.getCellValue('Eviction Case Number')}.

Please plan to arrive at court <i>at least</i> 15 minutes early to find parking and get to your courtroom. <b>Any other tips here?</b>

This message was sent by an automated system from https://npimemphis.org. Please do not reply. Thank you.`
    }
    buildEmail(rec) {
        return `Hello ${rec.getCellValue('AppFirstName')} ${rec.getCellValue('AppLastName')}, \
\
${this.buildBody(rec)}`
    }
    showEmail(rec) {
        console.log('To: ' + rec.getCellValue('ApplicantEmail'));
        console.log('From: do-not-reply@npimemphis.org');
        console.log('Subject: ' + 'Your court eviction hearing');
        console.log('Body: ' + this.buildEmail(rec));
    }
    runIt(query) {
        let alreadyMarkedRecords = query.records.filter(rec => {
            return (rec.getCellValue('Email For Automation')
                   )
        })
        for (let rec of alreadyMarkedRecords) {
            table.updateRecordAsync(rec, {'Email For Automation' : ''})
        }
        let filteredRecords = query.records.filter(rec => {
            return (!rec.getCellValue('Tenant Case Email Sent') &&
                    rec.getCellValue('Next Court Date') &&            
                    rec.getCellValue('Next Court Date Location') &&
                    rec.getCellValue('Next Court Date Room') &&
                    rec.getCellValue('ApplicantEmail') &&
                    rec.getCellValue('Eviction Case Number') &&
                    rec.getCellValue('Case Status (In Neighborly)') === 'Approved: Sent for legal'
                   )
        })
        let c = 0
        for (let rec of filteredRecords) {
            if (c === 0) {
                this.showEmail(rec);
            }
            let email = rec.getCellValue('ApplicantEmail')
            table.updateRecordAsync(rec, {'Email For Automation' : email})
            c++
        }
        console.log('Marked ' + c + ' applicants for automated email sending.');
    }
}
let table = base.getTable('All Applicants');
let query = await table.selectRecordsAsync({fields: table.fields});
new App1().runIt(query);