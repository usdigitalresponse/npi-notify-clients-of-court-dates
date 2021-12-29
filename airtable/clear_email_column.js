let table = base.getTable('All Applicants');
let query = await table.selectRecordsAsync({fields: table.fields});
let alreadyMarkedRecords = query.records.filter(rec => {
    return (rec.getCellValue('Email For Automation'))
})
let c1 = 0
for (let rec of alreadyMarkedRecords) {
    table.updateRecordAsync(rec, {'Email For Automation' : ''})
    c1++
}
console.log(c1 + ' Email For Automation cleared')