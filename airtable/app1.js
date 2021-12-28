class App1 {
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
            let judge = rec.getCellValue('Next Court Date Judge')
            if (!judge || judge === 'unassigned') {
                judge = ''
            }
            return (status_val.includes('Approved: Sent for legal') &&
                    caseNumber !== 'Not Found' &&
                    caseNumber !== '' &&
                   !rec.getCellValue('Tenant Case Email Sent') &&
                    rec.getCellValue('ApplicantEmail') &&
                    rec.getCellValue('Next Court Date') &&
                    rec.getCellValue('Next Court Date Location') &&
                    judge !== '' &&
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