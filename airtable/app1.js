class App1 {
    /**
    * @param {string | EvictionsMessages2Table_Record} rec
    */
    getCourtDate(rec) {
        const dateStr = rec.getCellValue('Confirmed Court Date')
        return new Date(dateStr).
                toLocaleDateString('en-us', 
                { weekday:"long", year:"numeric", month:"short", day:"numeric"}) 
    }
    /**
    * @param {string | EvictionsMessages2Table_Record} rec
    */
    buildBody(rec) {
        const theDate = this.getCourtDate(rec)
        return `You have an eviction hearing on ${theDate} \
at the ${rec.getCellValue('Next Court Date Location')}, \
room ${rec.getCellValue('Next Court Date Room')}.

Your case number is ${rec.getCellValue('Confirmed Case #')}. \
Please contact the courts at https://gs4.shelbycountytn.gov/8/Civil-Division if you have any questions.

This message was sent by an automated system from npimemphis.org. Please do not reply to it. Thank you.`
    }
    /**
    * @param {string | EvictionsMessages2Table_Record} rec
    */
    buildEmail(rec) {
        return `Dear ${rec.getCellValue('First')} ${rec.getCellValue('Last')},
${this.buildBody(rec)}`
    }
    /**
    * @param {string | EvictionsMessages2Table_Record} rec
    */
    sendEmail(rec) {
        console.log('To: ' + rec.getCellValue('Email'));
        console.log('From: do-not-reply@npimemphis.org');
        const theDate = this.getCourtDate(rec);

        console.log('Subject: ' + 'You have an eviction hearing on ' + theDate);
        console.log('Body: ' + this.buildEmail(rec));
    }
    /**
    * @param {string | EvictionsMessages2Table_Record} rec
    */
    sendSMS(rec) {
        console.log('To be texted to: ' + rec.getCellValue('Phone'));
        console.log(this.buildBody(rec));
    }
    /**
    * @param {EvictionsMessages2Table_RecordQueryResult} query
    */
    runIt(query) {
        let filteredRecords = query.records.filter(rec => {
            return !(rec.getCellValue('Date Email Sent') || rec.getCellValue('Date SMS Sent')) &&
            rec.getCellValue('Confirmed Court Date') &&
            rec.getCellValue('Next Court Date Location') &&
            rec.getCellValue('Next Court Date Room') &&
            rec.getCellValue('Confirmed Case #')
        })
        for (let rec of filteredRecords) {
            if (!rec.getCellValue('Date Email Sent') && rec.getCellValue('Email')) {
                this.sendEmail(rec);
            }
            if (!rec.getCellValue('Date SMS Sent') && rec.getCellValue('Phone')) {
                this.sendSMS(rec);
            }
        }
    }
}
let table = base.getTable('Evictions Messages 2');
let query = await table.selectRecordsAsync({fields: table.fields});
new App1().runIt(query);