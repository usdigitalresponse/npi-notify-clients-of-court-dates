class App1 {
    buildBody(rec) {
        return `You have an eviction hearing on ${rec.getCellValue('Next Court Date')} \
at building: ${rec.getCellValue('Next Court Date Location')}, \
room" ${rec.getCellValue('Next Court Date Room')}.

Your case number is ${rec.getCellValue('Eviction Case Number')}. \
Please contact the courts at https://gs4.shelbycountytn.gov/8/Civil-Division if you have any questions.

This message was sent by an automated system from npimemphis.org. Please do not reply to it. Thank you.`
    }
    buildEmail(rec) {
        return `Dear ${rec.getCellValue('AppFirstName')} ${rec.getCellValue('AppLastName')},
${this.buildBody(rec)}`
    }
    showEmail(rec) {
        console.log('To: ' + rec.getCellValue('ApplicantEmail'));
        console.log('From: do-not-reply@npimemphis.org');
        console.log('Subject: ' + 'You have an eviction hearing on ' + rec.getCellValue('Next Court Date'));
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
            return (!rec.getCellValue('Tenant Invitation Email Sent') &&
                    rec.getCellValue('Next Court Date') &&            
                    rec.getCellValue('Next Court Date Location') &&
                    rec.getCellValue('Next Court Date Room') &&
                    rec.getCellValue('ApplicantEmail') &&
                    rec.getCellValue('Eviction Case Number')
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