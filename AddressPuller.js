'use strict';
const fs = require('fs');
const https = require('https')

class Getter {
    Getter() {
        this.ret = 'empty result'
    }
    get(hostname, path) {
        const options = {
            hostname: hostname,
            port: 443,
            path: path,
            method: 'GET'
        }
        const req = https.request(options, res => {
            console.log(`res: ${res}`)
            console.log(`statusCode: ${res.statusCode}`)
            
            res.on('data', d => {
                process.stdout.write(d)
            })
        })          
        req.on('error', error => {
            console.error(error)
        })          
        req.end()
        return this.ret
    }    
}
class AddressPuller {
    constructor(host, path) {
        this.HOST = host
        this.PATH = path
    }
    pull() {
        let g = new Getter()
        let res = g.get(this.HOST, this.PATH)
        console.log('pulled: ' + res.substring(0, 128))
    }
}
class TransformerToAirtable {
    constructor() {
        this.minDate = new Date(3000, 0, 1)
        this.maxDate = new Date(1970, 0, 1)    
    }

    // for viewing possible field values
    displayValues(sourceData) {
        const parties = new Set()
        const docket_descriptions = new Set()
        for (const evictionCase of sourceData) {
            for (const party of evictionCase.parties) {
                parties.add(party.type)
            }
            for (const docket_entry of evictionCase.docket_entries) {
                docket_descriptions.add(docket_entry.description)
            }
        }
        console.log('Total cases: ' + sourceData.length)
        let i = 0
        for (const p of parties) {
            console.log(i + ' ' + p)
            i++
        }
        i = 0
        for (const d of docket_descriptions) {
            console.log(i + ' ' + d)
            i++
        }
    }
    extractFields(theMap, party) {
        if (!party) {
            return
        }
        let names = party.name.split(', ')
        if (names.length > 1) {
            theMap['FIRST NAME'] = names[1]
        }
        theMap['LAST NAME'] =names[0]
        let addressParts = party.address.split('\n')
        theMap['ADDRESS 1'] = addressParts[0]
        addressParts = addressParts[1].split(' ') 
        theMap['CITY' ] = addressParts[0]
        theMap['STATE' ] = addressParts[1]
        theMap['ZIP CODE' ] = addressParts[2]
    }
    createRow(evictionCase) {
        let thisDate = Date.parse(evictionCase.filing_date)
        if (thisDate < this.minDate) {
            this.minDate = new Date(evictionCase.filing_date)
        }
        if (thisDate > this.maxDate) {
            this.maxDate = new Date(evictionCase.filing_date)
        }
        let tenantMap = {
            'Eviction Case Number' : evictionCase.case_num,
            'Filed Date' : evictionCase.filing_date,
            'Case Title' : evictionCase.title
        }
        let defendant = null
        let plaintiff = null
        let attorney = null
        let proSe = null
        for (const party of evictionCase.parties) {
            switch (party.type) {
                case "DEFENDANT" : defendant = party; break
                case "PLAINTIFF" : plaintiff = party;  break
                case "ATTORNEY FOR PLAINTIFF" : attorney = party; break
                case "PRO SE LITIGANT" : proSe = party; break
            }
        }
        let landlord
        if (plaintiff) {
            landlord = plaintiff
        } else if (attorney) {
            landlord = attorney
        } else if (proSe) {
            landlord = proSe
        }
        for (const docket_entry of evictionCase.docket_entries) {
            if (docket_entry.description === 'POSSESSION $___& COST FED') {
                tenantMap['Settlement Date'] = docket_entry.date
                break
            }
        }
        this.extractFields(tenantMap, defendant)
        let landlordMap = {
            'eid' : landlord.eid,
            'Filed Date' : evictionCase.filing_date
        }
        this.extractFields(landlordMap, landlord)
        return [tenantMap, landlordMap]
    }
    doTransform(sourceData) {
        let tenants = []
        let landlords = []
        for (const evictionCase of sourceData) {
            let [ten, lan] = this.createRow(evictionCase)
            tenants.push(ten)
            landlords.push(lan)
        }
        return [tenants, landlords]
    }
    async loadTable(parties, tableName, keyName) {
        let table = base.getTable(tableName);
        for (party of parties) {
            let queryResult = await table.selectRecordsAsync();
            let record = queryResult.getRecord(keyName)
            if (record) {
                await table.updateRecordAsync(party);
            } else {
                await table.createRecordAsync(party);
            }
        }
    }
    transform() {
        let sourceData = JSON.parse(fs.readFileSync('private.json')) // new AddressPuller(theHostName, thePath).pull()
        let [tenants, landlords] = this.doTransform(sourceData)
        console.log('Processed ' + tenants.length + ' records.')
        console.log('First tenant: ' + JSON.stringify(tenants[0]))
        console.log('First landlord: ' + JSON.stringify(landlords[0]))
        console.log('min Filed Date: ' + this.minDate.toString())
        console.log('max Filed Date: ' + this.maxDate.toString())
//        await this.loadTable(tenants, 'Tenant Postcard Addresses', 'Eviction Case Number')
//        await this.loadTable(landlords, 'Landlords', 'eid')
    }
}
new TransformerToAirtable().transform()
